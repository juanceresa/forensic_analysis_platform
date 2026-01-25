"""Tests for narrative generation prompts."""

import pytest
from farmer_factory.narrative.prompts import NarrativePrompts


def test_prompts_initialization():
    """Test NarrativePrompts initialization."""
    prompts = NarrativePrompts()
    assert prompts is not None


def test_narrative_prompt_structure():
    """Test narrative prompt contains required constraints."""
    prompts = NarrativePrompts()

    graph_context = {
        "focal_entity": {
            "name": "Villa Aurelia",
            "type": "PROPERTY",
            "connections": 11
        },
        "entities": ["Mario Ceresa", "Juan Ceresa", "INRA"],
        "relations": [
            {"type": "OWNS", "source": "Mario Ceresa", "target": "Villa Aurelia"},
            {"type": "CONFISCATED", "source": "INRA", "target": "Villa Aurelia"}
        ],
        "documents": ["doc_001", "doc_012"]
    }

    prompt = prompts.build_narrative_prompt(graph_context)

    # Should contain forensic facts constraint
    assert "forensic" in prompt.lower() or "factual" in prompt.lower()
    # Should mention focal entity
    assert "Villa Aurelia" in prompt
    # Should prohibit legal conclusions
    assert "legal" in prompt.lower() or "conclusion" in prompt.lower()
    # Should require citations
    assert "citation" in prompt.lower() or "[①]" in prompt
    # Should emphasize expropriations
    assert "confiscation" in prompt.lower() or "expropriation" in prompt.lower()
    # Should request narrative voice
    assert "narrative" in prompt.lower() or "story" in prompt.lower()


def test_simple_entity_prompt():
    """Test prompt for simple entities (insufficient data)."""
    prompts = NarrativePrompts()

    simple_context = {
        "focal_entity": {
            "name": "Juan Mir Perez",
            "type": "PERSON"
        },
        "role": "Jefe del Departamento Legal del INRA",
        "document": "doc_012"
    }

    prompt = prompts.build_simple_narrative_prompt(simple_context)

    assert "Juan Mir Perez" in prompt
    assert "INRA" in prompt
