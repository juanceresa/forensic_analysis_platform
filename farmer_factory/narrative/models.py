"""Pydantic models for narrative generation output."""

from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field

from farmer_factory.structure.schema import VerificationTier


class EvidenceCitation(BaseModel):
    """Single piece of evidence supporting a claim."""

    doc_id: str = Field(description="Source document ID")
    page: Optional[int] = Field(default=None, description="Page number in document")
    quote: str = Field(description="Exact quote from document")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    verification_tier: VerificationTier = Field(description="Verification tier")
    ocr_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="OCR quality score"
    )


class FactualClaim(BaseModel):
    """Single fact in the narrative with supporting evidence."""

    claim_text: str = Field(description="The factual claim statement")
    citation_number: int = Field(description="Citation reference number")
    evidence: List[EvidenceCitation] = Field(
        description="Supporting evidence",
        min_length=1
    )
    temporal_context: Optional[str] = Field(
        default=None,
        description="Date/time context (e.g., '1956', 'Early 1960s')"
    )
    fact_type: Optional[str] = Field(
        default=None,
        description="Fact category (e.g., 'OWNERSHIP', 'TRANSFER', 'CONFISCATION')"
    )


class EventHighlight(BaseModel):
    """Special events that need prominent display (expropriations, sales, inheritances)."""

    event_type: Literal["CONFISCATED", "SOLD", "INHERITED"] = Field(
        description="Type of highlighted event"
    )
    summary: str = Field(description="Brief event summary")
    date: Optional[str] = Field(default=None, description="Event date if known")
    citation_number: int = Field(description="Citation reference number")
    evidence: List[EvidenceCitation] = Field(
        description="Supporting evidence",
        min_length=1
    )
    parties_involved: List[str] = Field(
        default_factory=list,
        description="Entity names involved in event"
    )


class NarrativeResult(BaseModel):
    """Complete narrative generation result."""

    # Metadata
    focal_entity_id: str = Field(description="ID of narrative focal point")
    focal_entity_name: str = Field(description="Name of focal entity")
    focal_entity_type: str = Field(description="Entity type (PROPERTY, PERSON, etc)")
    constellation_size: int = Field(description="Number of entities in context")
    generated_at: datetime = Field(default_factory=datetime.now)
    model_used: Literal["haiku", "sonnet"] = Field(description="LLM model used")

    # Content
    main_narrative: str = Field(
        description="Chronological narrative with inline citations [①]"
    )
    facts: List[FactualClaim] = Field(description="Structured factual claims")
    highlighted_events: List[EventHighlight] = Field(
        default_factory=list,
        description="Special events needing prominence"
    )

    # Quality indicators
    total_documents: int = Field(description="Number of source documents")
    total_citations: int = Field(description="Total evidence citations")
    date_range: Optional[str] = Field(
        default=None,
        description="Temporal span (e.g., '1952-1962')"
    )

    # Session tracking
    generation_cost: float = Field(
        default=0.0,
        description="Estimated API cost for this generation (USD)"
    )
    from_cache: bool = Field(
        default=False,
        description="Whether result came from cache"
    )

    # Flags
    is_simple_entity: bool = Field(
        default=False,
        description="True if insufficient data for full narrative"
    )
    quality_warning: Optional[str] = Field(
        default=None,
        description="Warning for low-quality data"
    )
