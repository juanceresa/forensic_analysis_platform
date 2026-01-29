"""Tests for batch narrative prompt builders."""

from farmer_factory.narrative.prompts import (
    CASE_SUMMARY_TEMPLATE,
    PERIOD_NARRATIVE_TEMPLATE,
    build_period_prompt,
    build_summary_prompt,
)


def test_period_prompt_contains_constraints():
    prompt = build_period_prompt(
        period_label="Post-War Era",
        period_range="1950-1959",
        documents=[
            {"id": "doc_001", "name": "Escritura 1952", "date": "1952-06-01", "document_type": "NOTARIAL"},
        ],
        entities=[
            {"id": "ent_001", "name": "Mario Ceresa", "entity_type": "PERSON"},
        ],
        relations=[
            {
                "source_name": "Mario Ceresa",
                "target_name": "Villa Aurelia",
                "relation_type": "OWNS",
                "date": "1952",
            },
        ],
    )
    assert "Post-War Era" in prompt
    assert "1950-1959" in prompt
    assert "Escritura 1952" in prompt
    assert "Mario Ceresa" in prompt
    assert "NEVER make legal conclusions" in prompt
    assert "NEVER infer beyond" in prompt


def test_period_prompt_highlights_confiscation():
    prompt = build_period_prompt(
        period_label="Expropriation Period",
        period_range="1959-1961",
        documents=[],
        entities=[],
        relations=[
            {
                "source_name": "INRA",
                "target_name": "Villa Aurelia",
                "relation_type": "CONFISCATED",
                "date": "1960",
            },
        ],
    )
    assert "CONFISCATION" in prompt


def test_period_prompt_no_special_events():
    prompt = build_period_prompt(
        period_label="Early Records",
        period_range="1910-1919",
        documents=[],
        entities=[],
        relations=[
            {"source_name": "A", "target_name": "B", "relation_type": "MENTIONS"},
        ],
    )
    assert "Special Events" in prompt
    assert "None" in prompt


def test_summary_prompt_contains_case_info():
    prompt = build_summary_prompt(
        case_id="CERESA-001",
        date_range="1940-1960",
        total_documents=12,
        total_entities=8,
        period_summaries=[
            {"label": "Post-War Era", "range": "1950-1959", "narrative": "Property changed hands."},
        ],
    )
    assert "CERESA-001" in prompt
    assert "1940-1960" in prompt
    assert "12" in prompt
    assert "Post-War Era" in prompt
    assert "NEVER make legal conclusions" in prompt


def test_templates_are_format_strings():
    """Templates should have expected placeholders."""
    assert "{period_label}" in PERIOD_NARRATIVE_TEMPLATE
    assert "{documents_context}" in PERIOD_NARRATIVE_TEMPLATE
    assert "{case_id}" in CASE_SUMMARY_TEMPLATE
    assert "{period_summaries}" in CASE_SUMMARY_TEMPLATE
