"""
Pydantic schema models for Civic Table knowledge graph.

Entity types and relation types are loaded dynamically from domain configuration.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Dynamic Type Helpers
# ============================================================================


def get_valid_entity_types() -> Set[str]:
    """
    Get valid entity types from domain config, or defaults if no domain active.

    Returns:
        Set of valid entity type strings
    """
    try:
        from farmer_factory.domains import domain_registry

        if domain_registry.is_active:
            return set(domain_registry.get_entity_types())
    except Exception:
        pass
    # Fallback defaults
    return {"PERSON", "PROPERTY", "ORGANIZATION", "LOCATION", "DOCUMENT"}


def get_valid_relation_types() -> Set[str]:
    """
    Get valid relation types from domain config, or defaults if no domain active.

    Returns:
        Set of valid relation type strings
    """
    try:
        from farmer_factory.domains import domain_registry

        if domain_registry.is_active:
            return set(domain_registry.get_relation_types())
    except Exception:
        pass
    # Fallback defaults
    return {
        "OWNS",
        "OWNED",
        "INHERITED",
        "SOLD",
        "SOLD_TO",
        "BOUGHT",
        "PURCHASED_FROM",
        "CONFISCATED",
        "SPOUSE_OF",
        "CHILD_OF",
        "HEIR_OF",
        "RELATED_TO",
        "BORDERS_NORTH",
        "BORDERS_SOUTH",
        "BORDERS_EAST",
        "BORDERS_WEST",
        "MENTIONED_IN",
        "WITNESSED",
        "WITNESSED_BY",
        "NOTARIZED",
        "NOTARIZED_BY",
        "ISSUED_BY",
        "REPRESENTED_BY",
        "EMPLOYED_BY",
        "LOCATED_IN",
        "REGISTERED_IN",
        "CREDITOR_OF",
        "DEBTOR_OF",
    }


def create_entity_type_enum():
    """Create EntityType enum from domain config."""
    types = get_valid_entity_types()
    return Enum("EntityType", {t: t for t in sorted(types)}, type=str)


def create_relation_type_enum():
    """Create RelationType enum from domain config."""
    types = get_valid_relation_types()
    return Enum("RelationType", {t: t for t in sorted(types)}, type=str)


# Create dynamic enums - these will use defaults until domain is set
EntityType = create_entity_type_enum()
RelationType = create_relation_type_enum()


def refresh_type_enums():
    """
    Refresh EntityType and RelationType enums from current domain config.

    Call this after setting the active domain to update the enums.
    """
    global EntityType, RelationType
    EntityType = create_entity_type_enum()
    RelationType = create_relation_type_enum()
    logger.debug(
        f"Refreshed enums: {len(EntityType.__members__)} entity types, "
        f"{len(RelationType.__members__)} relation types"
    )


# ============================================================================
# Verification
# ============================================================================


class VerificationTier(str, Enum):
    """Verification tier for entities and relations."""

    TIER_3_AI = "TIER_3_AI"
    TIER_2_ANALYST = "TIER_2_ANALYST"
    TIER_2_INSTITUTIONAL = "TIER_2_INSTITUTIONAL"
    TIER_1_CERTIFIED = "TIER_1_CERTIFIED"


class LocationNature(str, Enum):
    """
    Nature of a location for disambiguation.

    Based on Chilean KG paper recommendations for location disambiguation.
    Distinguishes between:
    - ADMINISTRATIVE: Political/jurisdictional (country, province, municipality)
    - GEOGRAPHIC: Physical features (river, mountain, bay)
    - PROPERTY: Named properties/estates (fincas, centrales, haciendas)
    """

    ADMINISTRATIVE = "ADMINISTRATIVE"
    GEOGRAPHIC = "GEOGRAPHIC"
    PROPERTY = "PROPERTY"


class OrganizationNature(str, Enum):
    """
    Nature of an organization for disambiguation.

    Helps distinguish between different types of organizations:
    - GOVERNMENT: State entities, registries, courts
    - BUSINESS: Companies, banks, commercial entities
    - RELIGIOUS: Churches, religious orders
    - PROFESSIONAL: Professional associations, colegios
    """

    GOVERNMENT = "GOVERNMENT"
    BUSINESS = "BUSINESS"
    RELIGIOUS = "RELIGIOUS"
    PROFESSIONAL = "PROFESSIONAL"


class Verification(BaseModel):
    """Verification metadata for entities and relations."""

    tier: VerificationTier
    confidence: float = Field(ge=0.0, le=1.0)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


# ============================================================================
# Entity Models
# ============================================================================


class BaseEntity(BaseModel):
    """Base class for all entity types."""

    id: str
    entity_type: str  # Validated against domain config
    verification: Verification
    extracted_from: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        valid_types = get_valid_entity_types()
        if v not in valid_types:
            raise ValueError(f"Invalid entity type '{v}'. Valid types: {valid_types}")
        return v


class Person(BaseEntity):
    """Person entity (owners, heirs, witnesses, notaries)."""

    entity_type: str = "PERSON"

    # Core identity
    name: str
    alternate_names: List[str] = Field(default_factory=list)

    # Demographics
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    nationality: Optional[str] = None
    residence: Optional[str] = None
    profession: Optional[str] = None
    marital_status: Optional[str] = None

    # Family relationships
    mother: Optional[str] = Field(default=None, description="Name of mother")
    father: Optional[str] = Field(default=None, description="Name of father")
    spouse: Optional[str] = Field(default=None, description="Name of spouse")
    children: List[str] = Field(default_factory=list, description="Names of children")
    siblings: List[str] = Field(default_factory=list, description="Names of siblings")

    # Roles
    roles: List[str] = Field(default_factory=list)


class Property(BaseEntity):
    """Property entity."""

    entity_type: str = "PROPERTY"

    # Identity
    name: Optional[str] = None
    property_type: Optional[str] = None

    # Location & Description
    location_id: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

    # Measurements
    area: Optional[float] = None
    area_unit: Optional[str] = None

    # Registry info
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None


class Organization(BaseEntity):
    """Organization entity."""

    entity_type: str = "ORGANIZATION"

    name: str
    org_type: Optional[str] = None
    location_id: Optional[str] = None
    address: Optional[str] = None
    nature: Optional[str] = Field(
        default=None,
        description="Organization nature for disambiguation (GOVERNMENT, BUSINESS, RELIGIOUS, PROFESSIONAL)"
    )


class Location(BaseEntity):
    """Location entity."""

    entity_type: str = "LOCATION"

    name: str
    location_type: Optional[str] = None
    parent_location_id: Optional[str] = None
    country: str = "Cuba"
    nature: Optional[str] = Field(
        default=None,
        description="Location nature for disambiguation (ADMINISTRATIVE, GEOGRAPHIC, PROPERTY)"
    )


class Document(BaseEntity):
    """Document entity (source documents for provenance)."""

    entity_type: str = "DOCUMENT"

    # Document identity
    title: Optional[str] = None
    document_type: str
    document_number: Optional[str] = None
    date: Optional[str] = None

    # Provenance
    issuer: Optional[str] = None
    location_id: Optional[str] = None

    # Processing
    file_path: str
    page_count: int
    ocr_text: Optional[str] = None
    language: str = "es"


# ============================================================================
# Relation Model
# ============================================================================


class Relation(BaseModel):
    """Relation between entities in the knowledge graph."""

    id: str
    type: str  # Validated against domain config
    source_id: str
    target_id: str
    verification: Verification

    # Context fields
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    property_id: Optional[str] = None
    document_id: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_relation_type(cls, v: str) -> str:
        valid_types = get_valid_relation_types()
        if v not in valid_types:
            raise ValueError(f"Invalid relation type '{v}'. Valid types: {valid_types}")
        return v


# ============================================================================
# Graph Export Models
# ============================================================================


class GraphMetadata(BaseModel):
    """Metadata for knowledge graph export."""

    case_id: str
    created_at: datetime
    updated_at: datetime
    factory_version: str
    entity_count: int
    relation_count: int
    document_count: int
    processing_stats: Dict[str, Any] = Field(default_factory=dict)
    verification_distribution: Dict[str, int] = Field(default_factory=dict)
    entity_type_summary: Dict[str, int] = Field(default_factory=dict)
    date_range: Optional[Dict[str, Optional[str]]] = None
    domain: Optional[str] = None  # Track which domain was used


class GraphExport(BaseModel):
    """Export format for graph_data.json."""

    metadata: GraphMetadata
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
