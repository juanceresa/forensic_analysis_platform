"""Pydantic models for dossier generation.

These models define the data contract between the preparer (which assembles
data from the knowledge graph) and the renderer (which generates LaTeX).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from farmer_factory.structure.schema import VerificationTier


class TimelineEvent(BaseModel):
    """Single event in the chronological timeline."""

    date: str | None = Field(default=None, description="ISO date or 'circa 1950s'")
    date_sortable: str | None = Field(default=None, description="ISO format for sorting")
    event_type: str = Field(description="ACQUISITION, BIRTH, DEATH, CONFISCATION, etc.")
    summary: str = Field(description="One-line description")
    entities_involved: list[str] = Field(default_factory=list, description="Entity names")
    source_doc_id: str | None = Field(default=None, description="Document proving this")
    verification_tier: VerificationTier = Field(default=VerificationTier.TIER_3_AI)


class FamilyMember(BaseModel):
    """Person in the family tree."""

    entity_id: str = Field(description="Entity ID from graph")
    name: str = Field(description="Full name")
    relation_to_claimant: str | None = Field(
        default=None, description="'grandfather', 'mother', etc."
    )
    birth_date: str | None = Field(default=None)
    death_date: str | None = Field(default=None)
    roles: list[str] = Field(default_factory=list, description="'owner', 'heir', 'witness'")
    verification_tier: VerificationTier = Field(default=VerificationTier.TIER_3_AI)


class FamilyTreeData(BaseModel):
    """Section: The Family."""

    primary_claimant: FamilyMember = Field(description="Focal family member")
    members: list[FamilyMember] = Field(default_factory=list, description="All family members")
    lineage_summary: str = Field(default="", description="Generated narrative of family line")


class PropertyData(BaseModel):
    """Section: The Property."""

    entity_id: str = Field(description="Entity ID from graph")
    name: str | None = Field(default=None, description="Property name if known")
    property_type: str | None = Field(default=None, description="Farm, house, etc.")
    address: str | None = Field(default=None)
    location_description: str = Field(
        default="", description="'Holguin, Oriente Province, Cuba'"
    )
    area: float | None = Field(default=None)
    area_unit: str | None = Field(default=None, description="hectares, caballerias, etc.")
    registry_info: str | None = Field(default=None, description="Folio, cadastral, etc.")
    description: str | None = Field(default=None, description="Historical context")
    map_image_path: str | None = Field(
        default=None, description="Path to map image from geolocation module"
    )
    verification_tier: VerificationTier = Field(default=VerificationTier.TIER_3_AI)


class EvidenceCitation(BaseModel):
    """Citation for a specific claim."""

    doc_id: str = Field(description="Document ID")
    doc_title: str | None = Field(default=None)
    page: int | None = Field(default=None)
    quote: str | None = Field(default=None, description="Exact quote from document")
    verification_tier: VerificationTier = Field(default=VerificationTier.TIER_3_AI)


class OwnershipPeriod(BaseModel):
    """Single period of ownership in the chain."""

    period_type: str = Field(description="ACQUISITION, OWNERSHIP, CONFISCATION")
    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)
    owner_names: list[str] = Field(default_factory=list)
    narrative: str = Field(default="", description="What happened during this period")
    evidence: list[EvidenceCitation] = Field(
        default_factory=list, description="Supporting documents"
    )


class DocumentSummary(BaseModel):
    """Single document in the evidence inventory."""

    doc_id: str = Field(description="Document ID")
    title: str | None = Field(default=None)
    document_type: str = Field(description="Deed, certificate, letter, etc.")
    date: str | None = Field(default=None)
    page_count: int = Field(default=1)
    what_it_proves: str = Field(default="", description="One-line summary")
    key_entities: list[str] = Field(default_factory=list, description="Entities mentioned")
    verification_tier: VerificationTier = Field(default=VerificationTier.TIER_3_AI)
    verification_confidence: float | None = Field(
        default=None, description="Pass-through from graph if available"
    )
    extracted_from: list[str] | None = Field(
        default=None, description="Source artifacts, if known"
    )


class VerificationStats(BaseModel):
    """Aggregate verification statistics."""

    total_data_points: int = Field(default=0)
    tier_distribution: dict[str, int] = Field(
        default_factory=dict, description="{'TIER_3_AI': 45, 'TIER_2_ANALYST': 5}"
    )
    overall_confidence: float = Field(default=0.0, description="Weighted average")
    section_breakdown: dict[str, dict[str, int]] = Field(
        default_factory=dict,
        description="{'timeline': {'TIER_3_AI': 10, ...}, ...}",
    )


# Standard disclaimer text
STANDARD_DISCLAIMER = """This dossier was prepared using automated document analysis and AI-assisted extraction.
All data points are classified by verification tier:

- TIER_3_AI: Automatically extracted, not yet verified
- TIER_2_ANALYST: Verified by trained analyst
- TIER_2_INSTITUTIONAL: Verified against institutional records
- TIER_1_CERTIFIED: Certified by licensed professional

This document presents forensic facts, not legal conclusions.
Consult qualified legal counsel for interpretation and strategy."""


class DossierData(BaseModel):
    """Complete prepared data for dossier generation.

    This is the main data structure passed from preparer to renderer.
    All section data is assembled here before LaTeX generation.
    """

    # Metadata
    case_id: str = Field(description="Case identifier")
    case_title: str = Field(description="'Ceresa Family Property Claim'")
    generated_at: datetime = Field(default_factory=datetime.now)

    # Executive Summary (LLM-generated with template constraints)
    executive_summary: str = Field(default="", description="2-paragraph summary")

    # Section data
    timeline: list[TimelineEvent] = Field(default_factory=list)
    family: FamilyTreeData
    property: PropertyData
    ownership_history: list[OwnershipPeriod] = Field(default_factory=list)
    documents: list[DocumentSummary] = Field(default_factory=list)

    # Verification
    verification_stats: VerificationStats = Field(default_factory=VerificationStats)
    disclaimer_text: str = Field(default=STANDARD_DISCLAIMER)
