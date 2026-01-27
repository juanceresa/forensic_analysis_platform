"""
Pydantic models for domain configuration.

These models define the schema for domain configuration files (YAML).
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Field and Entity Type Definitions
# ============================================================================


class FieldDefinition(BaseModel):
    """Definition of an entity field."""

    name: str
    type: str  # string, int, float, date, list[string], enum
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    extraction_hints: List[str] = Field(default_factory=list)
    values: Optional[List[str]] = None  # For enum types


class KnownEntity(BaseModel):
    """Pre-defined entity for a domain (e.g., known organizations)."""

    name: str
    aliases: List[str] = Field(default_factory=list)
    # Additional fields depending on entity type
    org_type: Optional[str] = None
    location_type: Optional[str] = None
    parent_location: Optional[str] = None


class EntityTypeConfig(BaseModel):
    """Configuration for an entity type."""

    description: str
    icon: str = ""
    color: str = "#6B7280"  # Default gray

    # Fields
    core_fields: List[FieldDefinition] = Field(default_factory=list)
    domain_fields: List[FieldDefinition] = Field(default_factory=list)

    # Known entities of this type
    known_entities: List[KnownEntity] = Field(default_factory=list)

    def get_all_fields(self) -> List[FieldDefinition]:
        """Get all fields (core + domain)."""
        return self.core_fields + self.domain_fields

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get a field by name."""
        for field in self.get_all_fields():
            if field.name == name:
                return field
        return None


# ============================================================================
# Relation Type Definitions
# ============================================================================


class RelationTypeConfig(BaseModel):
    """Configuration for a relation type."""

    description: str
    category: str  # ownership, transaction, family, document, etc.

    # Type constraints
    source_types: List[str]  # Entity types that can be source
    target_types: List[str]  # Entity types that can be target

    # Temporal behavior
    temporal: Literal["event", "state"] = "state"
    # event = needs date (SOLD, CONFISCATED)
    # state = date optional (OWNS, LOCATED_IN)

    # Display
    color: str = "#6B7280"
    icon: Optional[str] = None

    # Behavior
    symmetric: bool = False  # If true, A->B implies B->A
    creates_inverse: Optional[str] = None  # Creates inverse relation (SOLD -> BOUGHT)
    high_priority: bool = False  # Highlighted in narratives
    fallback: bool = False  # Used when specific type unclear

    # Extraction
    extraction_hints: List[str] = Field(default_factory=list)
    narrative_template: Optional[str] = None  # Special narrative formatting


class RelationCategory(BaseModel):
    """Category grouping for relation types."""

    label: str
    description: str
    high_priority: bool = False


# ============================================================================
# Domain Configuration
# ============================================================================


class TemporalRange(BaseModel):
    """Temporal range for a domain."""

    start: str  # Year
    end: str  # Year
    focus_period: Optional[str] = None  # e.g., "1959-1965"


class GeographicFocus(BaseModel):
    """Geographic focus for a domain."""

    countries: List[str]
    primary_regions: List[str] = Field(default_factory=list)


class SuccessCriteria(BaseModel):
    """Success criteria for a domain."""

    primary_goal: str
    verification_target: str = "TIER_2_ANALYST"
    completeness_indicators: List[str] = Field(default_factory=list)


class DomainConfig(BaseModel):
    """Complete domain configuration."""

    # Identity
    name: str
    code: str
    version: str
    description: str = ""

    # Language and locale
    primary_language: str = "en"
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])

    # Scope
    temporal_range: Optional[TemporalRange] = None
    geographic_focus: Optional[GeographicFocus] = None

    # Purpose
    use_cases: List[str] = Field(default_factory=list)
    success_criteria: Optional[SuccessCriteria] = None

    # Schema
    entity_types: Dict[str, EntityTypeConfig] = Field(default_factory=dict)
    relation_types: Dict[str, RelationTypeConfig] = Field(default_factory=dict)
    relation_categories: Dict[str, RelationCategory] = Field(default_factory=dict)

    # Prompts (loaded separately)
    prompts_dir: Optional[str] = None

    def get_entity_type(self, name: str) -> Optional[EntityTypeConfig]:
        """Get entity type configuration by name."""
        return self.entity_types.get(name)

    def get_relation_type(self, name: str) -> Optional[RelationTypeConfig]:
        """Get relation type configuration by name."""
        return self.relation_types.get(name)

    def get_temporal_relations(self) -> List[str]:
        """Get relation types that are events (need dates)."""
        return [
            name
            for name, config in self.relation_types.items()
            if config.temporal == "event"
        ]

    def get_state_relations(self) -> List[str]:
        """Get relation types that are states (dates optional)."""
        return [
            name
            for name, config in self.relation_types.items()
            if config.temporal == "state"
        ]

    def get_high_priority_relations(self) -> List[str]:
        """Get relation types that should be highlighted."""
        return [
            name for name, config in self.relation_types.items() if config.high_priority
        ]

    def get_extraction_hints(self, relation_type: str) -> List[str]:
        """Get extraction hints for a relation type."""
        config = self.get_relation_type(relation_type)
        return config.extraction_hints if config else []


# ============================================================================
# Verification Configuration (shared across domains)
# ============================================================================


class VerificationTierConfig(BaseModel):
    """Configuration for a verification tier."""

    name: str
    code: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    external: bool = False  # Requires external verification


class VerificationConfig(BaseModel):
    """Verification tier configuration."""

    tiers: Dict[str, VerificationTierConfig] = Field(default_factory=dict)

    def get_tier(self, code: str) -> Optional[VerificationTierConfig]:
        """Get verification tier by code."""
        return self.tiers.get(code)
