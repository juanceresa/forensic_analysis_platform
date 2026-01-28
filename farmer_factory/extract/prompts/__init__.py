"""Prompt templates for LLM extraction."""

from .helpers import (
    load_system_context,
    get_entity_extraction_hints,
    get_relation_extraction_hints,
    get_temporal_relations,
    get_state_relations,
    ocr_quality_description,
)
from .few_shot import (
    build_entity_prompt,
    build_relation_prompt,
)

__all__ = [
    # Helpers
    "load_system_context",
    "get_entity_extraction_hints",
    "get_relation_extraction_hints",
    "get_temporal_relations",
    "get_state_relations",
    "ocr_quality_description",
    # Prompts
    "build_entity_prompt",
    "build_relation_prompt",
]
