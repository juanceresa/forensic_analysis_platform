"""Pydantic models for case narrative generation output."""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class EventHighlight(BaseModel):
    """Key event requiring prominent display (expropriation, sale, inheritance)."""

    event_type: str = Field(description="Event type (e.g., CONFISCATED, SOLD, INHERITED)")
    summary: str = Field(description="Brief event summary")
    date: Optional[str] = Field(default=None, description="Event date if known")
    parties_involved: List[str] = Field(
        default_factory=list,
        description="Entity names involved in event",
    )


class NarrativePeriod(BaseModel):
    """AI-generated narrative for a single time period."""

    period_id: str = Field(description="Period identifier (e.g., '1950-1959')")
    label: str = Field(description="Human-readable period label")
    narrative: str = Field(description="AI-generated prose narrative for this period")
    document_ids: List[str] = Field(
        default_factory=list,
        description="Document IDs referenced in this period",
    )
    entity_ids: List[str] = Field(
        default_factory=list,
        description="Entity IDs referenced in this period",
    )
    highlighted_events: List[EventHighlight] = Field(
        default_factory=list,
        description="Key events in this period",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Relation IDs and event summaries used as evidence",
    )


class NarrativeMetadata(BaseModel):
    """Provenance metadata for the generated narrative."""

    case_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(description="Primary model used for generation")
    model_version: Optional[str] = Field(default=None, description="Model version string")
    prompt_hash: Optional[str] = Field(
        default=None,
        description="Hash of prompt templates for reproducibility",
    )
    generation_cost: float = Field(default=0.0, description="Total generation cost in USD")
    factory_version: str = Field(default="1.6.0", description="Factory version")
    verification_tier: str = Field(
        default="TIER_3_AI",
        description="All narrative content is TIER_3_AI",
    )


class CaseNarrative(BaseModel):
    """Complete case narrative — the family's story told through documents over time."""

    metadata: NarrativeMetadata
    case_summary: str = Field(description="Overall case narrative summary")
    periods: List[NarrativePeriod] = Field(
        default_factory=list,
        description="Per-period narratives in chronological order",
    )
