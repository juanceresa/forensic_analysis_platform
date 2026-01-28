"""Zero-shot prompt templates without examples (cost-optimized).

Based on Chilean KG paper methodology (arXiv:2408.11975).
Uses JSON schema specification without example values.
"""

import json
import logging
from typing import List

from farmer_factory.structure.schema import BaseEntity
from farmer_factory.domains import domain_registry
from .helpers import (
    load_system_context,
    get_relation_extraction_hints,
    ocr_quality_description,
)

logger = logging.getLogger(__name__)


def build_entity_prompt_zero_shot(
    text: str,
    document_id: str,
    document_type: str = "unknown",
    ocr_quality: float = 0.0,
) -> str:
    """
    Build zero-shot entity extraction prompt (no examples).

    Significantly shorter prompt for cost reduction.
    Based on Chilean KG paper methodology.

    Args:
        text: OCR-extracted text
        document_id: Document identifier
        document_type: Type of document
        ocr_quality: OCR confidence score

    Returns:
        Formatted prompt string
    """
    quality_desc = ocr_quality_description(ocr_quality)
    system_context = load_system_context()
    context_section = f"\n{system_context}\n" if system_context else ""

    prompt = f"""{context_section}Extract entities from this historical Cuban property document. Return JSON only.

ENTITY TYPES AND REQUIRED FIELDS:

PERSON: name (string), alternate_names (string[]), birth_date, death_date, nationality, residence, profession, marital_status, mother, father, spouse, children (string[]), siblings (string[]), roles (string[]), confidence (0-1), context (quote)

PROPERTY: name, property_type, location, address, description, area (number), area_unit, registry_number, cadastral_info, folio_number, confidence, context

ORGANIZATION: name, org_type, location, address, confidence, context

LOCATION: name, location_type, parent_location, country, confidence, context

RULES:
- Extract only explicit information from text
- Preserve Spanish names exactly
- Use null for missing fields, [] for empty lists
- Family relationships: look for "hijo de", "casado con", "esposa de"
- confidence: 0.0-1.0 based on text clarity

Document: {document_id} | Type: {document_type} | OCR: {quality_desc}

TEXT:
{text}

OUTPUT JSON:
{{"entities": [...], "dates": [...], "monetary_values": [...], "registry_refs": [...], "document_date": null, "document_date_confidence": null, "extraction_notes": ""}}"""
    return prompt


def build_relation_prompt_zero_shot(
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    document_type: str = "unknown",
) -> str:
    """
    Build zero-shot relation extraction prompt (no examples).

    Args:
        text: OCR-extracted text
        entities: Previously extracted entities
        document_id: Document identifier
        document_type: Type of document

    Returns:
        Formatted prompt string
    """
    entities_list = [
        {"id": e.id, "type": e.entity_type, "name": getattr(e, "name", str(e.id))}
        for e in entities
    ]
    entities_json = json.dumps(entities_list, indent=2, ensure_ascii=False)

    system_context = load_system_context()
    context_section = f"\n{system_context}\n" if system_context else ""

    # Build relation types from domain config
    relation_hints = get_relation_extraction_hints()
    if domain_registry.is_active and relation_hints:
        rel_types = ", ".join(domain_registry.active.relation_types.keys())
    else:
        rel_types = "OWNS, SOLD, BOUGHT, INHERITED, CONFISCATED, WITNESSED, NOTARIZED, REGISTERED_IN, LOCATED_IN, EMPLOYED_BY, RELATED_TO"

    prompt = f"""{context_section}Extract relationships between entities from this document. Return JSON only.

RELATION TYPES: {rel_types}

RELATION SCHEMA:
relation_type (string), source_entity (name), target_entity (name), confidence (0-1), temporal ({{start_date, end_date, ongoing, date_precision}}), evidence (quote), notes

RULES:
- Only extract explicit relationships from text
- temporal.date_precision: "exact", "month", "year", "decade", "unknown"
- If no relations found, return empty array

Document: {document_id}

ENTITIES:
{entities_json}

TEXT:
{text}

OUTPUT JSON:
{{"relations": [...], "extraction_notes": ""}}"""
    return prompt
