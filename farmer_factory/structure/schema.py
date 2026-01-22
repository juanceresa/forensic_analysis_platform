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
