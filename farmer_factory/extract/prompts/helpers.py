"""Helper functions for prompt building."""

import logging
from pathlib import Path
from typing import Dict, List, Set

from farmer_factory.domains import domain_registry

logger = logging.getLogger(__name__)


def get_temporal_relations() -> Set[str]:
    """Get temporal relation types from active domain config."""
    if not domain_registry.is_active:
        logger.warning("No active domain - using default temporal relations")
        return {"SOLD", "BOUGHT", "INHERITED", "CONFISCATED", "WITNESSED", "NOTARIZED"}
    return set(domain_registry.get_temporal_relations())


def get_state_relations() -> Set[str]:
    """Get state relation types from active domain config."""
    if not domain_registry.is_active:
        logger.warning("No active domain - using default state relations")
        return {"OWNS", "LOCATED_IN", "EMPLOYED_BY", "RELATED_TO", "REGISTERED_IN"}
    return set(domain_registry.get_state_relations())


def load_system_context() -> str:
    """Load system context from active domain's prompts directory."""
    if not domain_registry.is_active:
        logger.warning("No active domain - cannot load system context")
        return ""

    prompts_dir = domain_registry.active.prompts_dir
    if not prompts_dir:
        return ""

    context_file = Path(prompts_dir) / "system_context.txt"
    if context_file.exists():
        logger.debug(f"Loading system context from {context_file}")
        return context_file.read_text(encoding="utf-8")

    logger.debug(f"System context file not found: {context_file}")
    return ""


def get_entity_extraction_hints() -> Dict[str, Dict[str, List[str]]]:
    """Get extraction hints for all entity types from domain config."""
    if not domain_registry.is_active:
        return {}

    hints = {}
    for entity_type, config in domain_registry.active.entity_types.items():
        hints[entity_type] = {}
        for field in config.get_all_fields():
            if field.extraction_hints:
                hints[entity_type][field.name] = field.extraction_hints

    return hints


def get_relation_extraction_hints() -> Dict[str, List[str]]:
    """Get extraction hints for all relation types from domain config."""
    if not domain_registry.is_active:
        return {}

    hints = {}
    for rel_type, config in domain_registry.active.relation_types.items():
        if config.extraction_hints:
            hints[rel_type] = config.extraction_hints

    return hints


def ocr_quality_description(ocr_quality: float) -> str:
    """Map OCR quality score to human-readable description."""
    if ocr_quality >= 0.9:
        return "High (clear text)"
    elif ocr_quality >= 0.7:
        return "Medium (some unclear characters)"
    elif ocr_quality >= 0.5:
        return "Low (multiple unclear sections)"
    else:
        return "Very Low (significant OCR challenges)"
