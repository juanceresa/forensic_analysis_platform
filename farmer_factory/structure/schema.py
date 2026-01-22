"""
Pydantic schema models for Civic Table knowledge graph.

Defines entity types, relation types, and validation rules.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class VerificationTier(str, Enum):
    """Verification tier for entities and relations."""
    TIER_3_AI = "TIER_3_AI"
    TIER_2_ANALYST = "TIER_2_ANALYST"
    TIER_2_INSTITUTIONAL = "TIER_2_INSTITUTIONAL"
    TIER_1_CERTIFIED = "TIER_1_CERTIFIED"


class Verification(BaseModel):
    """Verification metadata for entities and relations."""
    tier: VerificationTier
    confidence: float = Field(ge=0.0, le=1.0)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


class EntityType(str, Enum):
    """Entity types in the knowledge graph."""
    PERSON = "PERSON"
    PROPERTY = "PROPERTY"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DOCUMENT = "DOCUMENT"


class BaseEntity(BaseModel):
    """Base class for all entity types."""
    id: str
    entity_type: EntityType
    verification: Verification
    extracted_from: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class Person(BaseEntity):
    """Person entity (owners, heirs, witnesses, notaries)."""
    entity_type: Literal[EntityType.PERSON] = EntityType.PERSON

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

    # Roles
    roles: List[str] = Field(default_factory=list)


class Property(BaseEntity):
    """Property entity (fincas, haciendas, urban properties)."""
    entity_type: Literal[EntityType.PROPERTY] = EntityType.PROPERTY

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
    """Organization entity (banks, courts, government agencies)."""
    entity_type: Literal[EntityType.ORGANIZATION] = EntityType.ORGANIZATION

    name: str
    org_type: Optional[str] = None
    location_id: Optional[str] = None
    address: Optional[str] = None


class Location(BaseEntity):
    """Location entity (cities, provinces, neighborhoods)."""
    entity_type: Literal[EntityType.LOCATION] = EntityType.LOCATION

    name: str
    location_type: Optional[str] = None
    parent_location_id: Optional[str] = None
    country: str = "Cuba"


class Document(BaseEntity):
    """Document entity (source documents for provenance)."""
    entity_type: Literal[EntityType.DOCUMENT] = EntityType.DOCUMENT

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


class RelationType(str, Enum):
    """Relation types in the knowledge graph."""
    # Property Ownership
    OWNS = "OWNS"
    OWNED = "OWNED"
    INHERITED = "INHERITED"
    SOLD_TO = "SOLD_TO"
    PURCHASED_FROM = "PURCHASED_FROM"

    # Family Relations
    SPOUSE_OF = "SPOUSE_OF"
    CHILD_OF = "CHILD_OF"
    HEIR_OF = "HEIR_OF"

    # Property Boundaries
    BORDERS_NORTH = "BORDERS_NORTH"
    BORDERS_SOUTH = "BORDERS_SOUTH"
    BORDERS_EAST = "BORDERS_EAST"
    BORDERS_WEST = "BORDERS_WEST"

    # Document Relations
    MENTIONED_IN = "MENTIONED_IN"
    WITNESSED_BY = "WITNESSED_BY"
    NOTARIZED_BY = "NOTARIZED_BY"
    ISSUED_BY = "ISSUED_BY"

    # Professional/Organizational
    REPRESENTED_BY = "REPRESENTED_BY"
    EMPLOYED_BY = "EMPLOYED_BY"

    # Financial
    CREDITOR_OF = "CREDITOR_OF"
    DEBTOR_OF = "DEBTOR_OF"


class Relation(BaseModel):
    """Relation between entities in the knowledge graph."""
    id: str
    type: RelationType
    source_id: str
    target_id: str
    verification: Verification

    # Context fields
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    property_id: Optional[str] = None
    document_id: Optional[str] = None
    notes: Optional[str] = None
