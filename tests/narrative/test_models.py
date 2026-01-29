"""Tests for batch case narrative Pydantic models."""

import json
from datetime import datetime

from farmer_factory.narrative.models import (
    CaseNarrative,
    EventHighlight,
    NarrativeMetadata,
    NarrativePeriod,
)


def test_event_highlight_minimal():
    event = EventHighlight(event_type="CONFISCATED", summary="State confiscated Villa")
    assert event.event_type == "CONFISCATED"
    assert event.date is None
    assert event.parties_involved == []


def test_event_highlight_full():
    event = EventHighlight(
        event_type="SOLD",
        summary="Garcia sold to Lopez",
        date="1952-03-15",
        parties_involved=["Garcia", "Lopez"],
    )
    assert event.date == "1952-03-15"
    assert len(event.parties_involved) == 2


def test_narrative_period_serialization():
    period = NarrativePeriod(
        period_id="1950-1959",
        label="Post-War Era",
        narrative="Villa Aurelia first appears in the record...",
        document_ids=["doc_001", "doc_002"],
        entity_ids=["ent_001"],
        highlighted_events=[
            EventHighlight(event_type="SOLD", summary="Property sold"),
        ],
        evidence=["doc:doc_001", "rel:SOLD:Garcia->Lopez"],
    )
    data = json.loads(period.model_dump_json())
    assert data["period_id"] == "1950-1959"
    assert len(data["highlighted_events"]) == 1
    assert len(data["evidence"]) == 2


def test_narrative_metadata_defaults():
    meta = NarrativeMetadata(case_id="TEST-001", model_used="sonnet")
    assert meta.verification_tier == "TIER_3_AI"
    assert meta.factory_version == "1.6.0"
    assert meta.generation_cost == 0.0
    assert isinstance(meta.generated_at, datetime)


def test_case_narrative_roundtrip():
    narrative = CaseNarrative(
        metadata=NarrativeMetadata(
            case_id="TEST-001",
            model_used="sonnet",
            generation_cost=0.05,
        ),
        case_summary="The documentary record spans 1940-1960.",
        periods=[
            NarrativePeriod(
                period_id="1940-1949",
                label="Pre-War Period",
                narrative="Early records show...",
            ),
            NarrativePeriod(
                period_id="1950-1959",
                label="Post-War Era",
                narrative="Property transfers occurred...",
            ),
        ],
    )
    json_str = narrative.model_dump_json(indent=2)
    restored = CaseNarrative.model_validate_json(json_str)
    assert restored.case_summary == narrative.case_summary
    assert len(restored.periods) == 2
    assert restored.metadata.generation_cost == 0.05


def test_empty_narrative():
    narrative = CaseNarrative(
        metadata=NarrativeMetadata(case_id="EMPTY", model_used="none"),
        case_summary="No documents.",
        periods=[],
    )
    assert len(narrative.periods) == 0
