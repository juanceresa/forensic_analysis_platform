"""Pydantic models for LLM extraction results."""

from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class IntermediateEntityType(str, Enum):
    """Entity types from PROMPTS.md extraction schema."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROPERTY = "PROPERTY"
    LOCATION = "LOCATION"
    DATE = "DATE"
    MONETARY_VALUE = "MONETARY_VALUE"
    REGISTRY_REFERENCE = "REGISTRY_REFERENCE"


# ============================================================================
# Structured Entity Extraction Models
# ============================================================================

class PersonExtraction(BaseModel):
    """Structured Person entity extraction."""
    entity_type: Literal["PERSON"] = "PERSON"

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

    # Family relationships (names as strings)
    mother: Optional[str] = None
    father: Optional[str] = None
    spouse: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    siblings: List[str] = Field(default_factory=list)

    # Roles
    roles: List[str] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this person")
    notes: Optional[str] = None

    @field_validator("alternate_names", "children", "siblings", "roles", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        """Coerce null/None from LLM response to empty list."""
        return v if v is not None else []


class PropertyExtraction(BaseModel):
    """Structured Property entity extraction."""
    entity_type: Literal["PROPERTY"] = "PROPERTY"

    # Identity
    name: Optional[str] = None
    property_type: Optional[str] = None

    # Location & Description
    location: Optional[str] = Field(None, description="Location name (will be linked to Location entity)")
    address: Optional[str] = None
    description: Optional[str] = None

    # Measurements
    area: Optional[float] = None
    area_unit: Optional[str] = None

    # Registry info
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this property")
    notes: Optional[str] = None


class OrganizationExtraction(BaseModel):
    """Structured Organization entity extraction."""
    entity_type: Literal["ORGANIZATION"] = "ORGANIZATION"

    name: str
    org_type: Optional[str] = None
    location: Optional[str] = Field(None, description="Location name (will be linked to Location entity)")
    address: Optional[str] = None

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this organization")
    notes: Optional[str] = None


class LocationExtraction(BaseModel):
    """Structured Location entity extraction."""
    entity_type: Literal["LOCATION"] = "LOCATION"

    name: str
    location_type: Optional[str] = None
    parent_location: Optional[str] = Field(None, description="Parent location name (e.g., 'Camagüey' for 'Florida')")
    country: str = "Cuba"

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this location")
    notes: Optional[str] = None


# Union type for structured entities
StructuredEntity = PersonExtraction | PropertyExtraction | OrganizationExtraction | LocationExtraction


class StructuredEntityExtractionResult(BaseModel):
    """Result from Claude structured entity extraction."""
    entities: List[StructuredEntity]
    dates: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted dates")
    monetary_values: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted monetary values")
    registry_refs: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted registry references")
    document_date: Optional[str] = None
    document_date_confidence: Optional[float] = None
    extraction_notes: Optional[str] = None


class TemporalInfo(BaseModel):
    """Temporal information for a relation."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ongoing: bool = False
    date_precision: Literal["exact", "month", "year", "decade", "unknown"] = "unknown"


class ExtractedRelation(BaseModel):
    """Single relation extracted from document (intermediate format)."""
    relation_type: str  # Will be validated against RelationType enum
    source_entity: str  # Entity name as string (not ID yet)
    target_entity: str  # Entity name as string (not ID yet)
    confidence: float = Field(ge=0.0, le=1.0)
    temporal: Optional[TemporalInfo] = None
    evidence: str  # Quote from document
    notes: Optional[str] = None


class RelationExtractionResult(BaseModel):
    """Result from Claude relation extraction (intermediate format)."""
    relations: List[ExtractedRelation]
    extraction_notes: Optional[str] = None
