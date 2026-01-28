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
from .zero_shot import (
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
)

__all__ = [
    # Helpers
    "load_system_context",
    "get_entity_extraction_hints",
    "get_relation_extraction_hints",
    "get_temporal_relations",
    "get_state_relations",
    "ocr_quality_description",
    # Zero-shot prompts (default - more effective and cost-efficient)
    "build_entity_prompt_zero_shot",
    "build_relation_prompt_zero_shot",
    # Few-shot prompts (kept for reference, not used by default)
    "build_entity_prompt",
    "build_relation_prompt",
]
