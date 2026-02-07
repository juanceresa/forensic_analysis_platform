"""Pydantic models for case narrative generation output."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# --- Document Analysis Models ---

class RelevanceLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class OcrQuality(str, Enum):
    EXCELLENT = "EXCELLENT"  # >0.90
    GOOD = "GOOD"            # 0.75-0.90
    FAIR = "FAIR"            # 0.60-0.75
    POOR = "POOR"            # <0.60


class ClaimRelevance(BaseModel):
    level: RelevanceLevel
    reasoning: str


class QualityNotes(BaseModel):
    ocr_quality: OcrQuality
    missing_information: list[str] = []
    verification_needed: list[str] = []


class GenerationMetadata(BaseModel):
    generated_at: str  # ISO 8601 timestamp
    model: str  # e.g., "claude-haiku-4-5-20251001"
    prompt_version: str  # e.g., "1.0"


class DocumentAnalysis(BaseModel):
    document_type: str
    executive_summary: str
    claim_relevance: ClaimRelevance
    key_facts: list[str] = []
    cross_references: list[str] = []
    quality_notes: QualityNotes
    source_docs: list[str] = []
    _metadata: GenerationMetadata


# --- Case Narrative Models ---


class EventHighlight(BaseModel):
    """Key event requiring prominent display (expropriation, sale, inheritance)."""

    event_type: str = Field(description="Event type (e.g., CONFISCATED, SOLD, INHERITED)")
    summary: str = Field(description="Brief event summary")
    date: Optional[str] = Field(default=None, description="Event date if known")
    parties_involved: List[str] = Field(
        default_factory=list,
        description="Entity names involved in event",
    )


class ForensicObservation(BaseModel):
    """Forensic observation flagged by the AI during narrative generation."""

    observation: str = Field(description="The forensic observation text")
    severity: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        default="MEDIUM", description="Severity/importance level"
    )


class InlineEntity(BaseModel):
    """Entity reference found inline within narrative prose."""

    name: str = Field(description="Entity name as it appears in the narrative")
    entity_id: str = Field(description="Entity ID from the knowledge graph")
    entity_type: str = Field(description="Entity type (PERSON, PROPERTY, etc.)")


class NarrativePeriod(BaseModel):
    """AI-generated narrative for a single time period."""

    period_id: str = Field(description="Period identifier (e.g., '1950-1959')")
    label: str = Field(description="Human-readable period label")
    title: str = Field(default="", description="Short evocative LLM-generated title")
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
    inline_entities: List[InlineEntity] = Field(
        default_factory=list,
        description="Entities whose names appear in the narrative prose",
    )
    forensic_observations: List[ForensicObservation] = Field(
        default_factory=list,
        description="AI-flagged forensic observations (discrepancies, patterns)",
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
