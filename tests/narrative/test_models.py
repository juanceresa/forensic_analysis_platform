"""Tests for narrative generation data models."""

import pytest
from datetime import datetime
from farmer_factory.narrative.models import (
    EvidenceCitation,
    FactualClaim,
    NarrativeResult,
    EventHighlight
)
from farmer_factory.structure.schema import VerificationTier


def test_evidence_citation_creation():
    """Test EvidenceCitation model creation."""
    citation = EvidenceCitation(
        doc_id="doc_001",
        page=2,
        quote="Mario Ceresa, propietario de Villa Aurelia",
        confidence=0.92,
        verification_tier=VerificationTier.TIER_2_ANALYST,
        ocr_confidence=0.88
    )

    assert citation.doc_id == "doc_001"
    assert citation.page == 2
    assert citation.confidence == 0.92
    assert citation.verification_tier == VerificationTier.TIER_2_ANALYST


def test_event_highlight_creation():
    """Test EventHighlight model for special events."""
    highlight = EventHighlight(
        event_type="CONFISCATED",
        summary="INRA confiscated 12.99 caballerías under Agrarian Reform Law",
        date="1960",
        citation_number=4,
        evidence=[
            EvidenceCitation(
                doc_id="doc_012",
                quote="confiscated by INRA",
                confidence=0.74,
                verification_tier=VerificationTier.TIER_3_AI
            )
        ]
    )

    assert highlight.event_type == "CONFISCATED"
    assert highlight.citation_number == 4
    assert len(highlight.evidence) == 1


def test_factual_claim_creation():
    """Test FactualClaim model."""
    claim = FactualClaim(
        claim_text="Mario Ceresa owned Villa Aurelia",
        citation_number=1,
        evidence=[
            EvidenceCitation(
                doc_id="doc_003",
                page=2,
                quote="Mario Ceresa, propietario",
                confidence=0.92,
                verification_tier=VerificationTier.TIER_2_ANALYST
            )
        ],
        temporal_context="1952",
        fact_type="OWNERSHIP"
    )

    assert claim.claim_text == "Mario Ceresa owned Villa Aurelia"
    assert claim.temporal_context == "1952"
    assert len(claim.evidence) == 1


def test_narrative_result_creation():
    """Test NarrativeResult model."""
    result = NarrativeResult(
        focal_entity_id="prop_villa_aurelia_001",
        focal_entity_name="Villa Aurelia",
        focal_entity_type="PROPERTY",
        constellation_size=15,
        model_used="sonnet",
        main_narrative="Villa Aurelia was a 59.28 caballería estate [①].",
        facts=[
            FactualClaim(
                claim_text="Estate size was 59.28 caballerías",
                citation_number=1,
                evidence=[
                    EvidenceCitation(
                        doc_id="doc_003",
                        quote="59.28 caballerías",
                        confidence=0.92,
                        verification_tier=VerificationTier.TIER_2_ANALYST
                    )
                ]
            )
        ],
        total_documents=8,
        total_citations=12,
        date_range="1952-1962",
        generation_cost=0.015
    )

    assert result.focal_entity_name == "Villa Aurelia"
    assert result.model_used == "sonnet"
    assert result.generation_cost == 0.015
    assert not result.from_cache
