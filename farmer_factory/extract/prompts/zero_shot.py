"""Zero-shot prompt templates without examples (cost-optimized).

Based on Chilean KG paper methodology (arXiv:2408.11975).
Uses JSON schema specification without example values.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, List

from farmer_factory.structure.schema import BaseEntity
from farmer_factory.domains import domain_registry
from .helpers import (
    load_system_context,
    get_relation_extraction_hints,
    ocr_quality_description,
)

if TYPE_CHECKING:
    from farmer_factory.intake.manifest import CaseFocus

logger = logging.getLogger(__name__)


def build_cleanup_prompt(
    text: str,
    document_id: str,
    ocr_quality: float = 0.0,
    detected_language: str = "unknown",
) -> str:
    """
    Build prompt for LLM-powered OCR text cleanup.

    Instructs the LLM to fix OCR noise while preserving original content.

    Args:
        text: Raw OCR text to clean
        document_id: Document identifier for context
        ocr_quality: OCR confidence score
        detected_language: ISO language code from OCR

    Returns:
        Formatted prompt string
    """
    quality_desc = ocr_quality_description(ocr_quality)
    system_context = load_system_context()
    context_section = f"\n{system_context}\n" if system_context else ""

    lang_hint = ""
    if detected_language and detected_language not in ("unknown", "und"):
        lang_hint = f"\nDetected language: {detected_language}. Preserve the original language exactly."

    prompt = f"""{context_section}You are an OCR text cleanup specialist for degraded historical documents.

TASK: Clean the following OCR-extracted text from a historical document. The OCR confidence is {quality_desc} ({ocr_quality:.0%}).{lang_hint}

RULES:
- Fix broken/hyphenated words across line breaks (e.g., "Far-\\nmacia" → "Farmacia")
- Remove OCR noise and artifacts: random characters, reversed bleed-through text, stray symbols
- Restore proper paragraph breaks following the document's logical sections
- Preserve the original language exactly — do NOT translate or paraphrase
- Keep ALL names, dates, numbers, addresses, and legal terms verbatim
- Mark genuinely unreadable sections as [ilegible]
- Do NOT add any information not present in the original text
- Do NOT wrap the output in JSON or any other format

Return ONLY the cleaned text, nothing else.

Document: {document_id} | OCR Quality: {quality_desc}

RAW OCR TEXT:
{text}

CLEANED TEXT:"""
    return prompt


def build_entity_prompt_zero_shot(
    text: str,
    document_id: str,
    document_type: str = "unknown",
    ocr_quality: float = 0.0,
    case_focus: CaseFocus | None = None,
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
        case_focus: Optional case-level focus configuration

    Returns:
        Formatted prompt string
    """
    quality_desc = ocr_quality_description(ocr_quality)
    system_context = load_system_context()
    context_section = f"\n{system_context}\n" if system_context else ""

    focus_section = ""
    if case_focus is not None:
        focus_text = case_focus.to_prompt_section()
        if focus_text:
            focus_section = f"\n{focus_text}\n"

    prompt = f"""{context_section}{focus_section}Extract entities from this historical Cuban property document. Return JSON only.

ENTITY TYPES AND REQUIRED FIELDS:

PERSON: name (string), alternate_names (string[]), birth_date, death_date, nationality, residence, profession, marital_status, mother, father, spouse, children (string[]), siblings (string[]), roles (string[]), confidence (0-1), context (quote)

PROPERTY: name, property_type, location, address, description, area (number), area_unit, registry_number, cadastral_info, folio_number, confidence, context

ORGANIZATION: name, org_type, location, address, confidence, context

LOCATION: name, location_type, parent_location, country, confidence, context

RULES:
- Extract ALL entity types present in the document, not just PERSON. Property documents typically contain PROPERTY and LOCATION entities — do not omit them.
- Extract only explicit information from text
- Preserve Spanish names exactly
- Use null for missing fields, [] for empty lists
- Family relationships: look for "hijo de", "casado con", "esposa de"
- Entity fields like spouse, mother, father are informational attributes from text.
  They do NOT create relation assertions — relations are extracted separately.
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
    case_focus: CaseFocus | None = None,
) -> str:
    """
    Build zero-shot relation extraction prompt (no examples).

    Args:
        text: OCR-extracted text
        entities: Previously extracted entities
        document_id: Document identifier
        document_type: Type of document
        case_focus: Optional case-level focus configuration

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

    focus_section = ""
    if case_focus is not None:
        focus_text = case_focus.to_prompt_section()
        if focus_text:
            focus_section = f"\n{focus_text}\n"

    # Build relation types from domain config
    relation_hints = get_relation_extraction_hints()
    if domain_registry.is_active and relation_hints:
        rel_types = ", ".join(domain_registry.active.relation_types.keys())
    else:
        rel_types = "OWNS, SOLD, BOUGHT, INHERITED, CONFISCATED, WITNESSED, NOTARIZED, REGISTERED_IN, LOCATED_IN, EMPLOYED_BY, RELATED_TO"

    prompt = f"""{context_section}{focus_section}Extract relationships between entities from this document. Return JSON only.

RELATION TYPES: {rel_types}

RELATION SCHEMA:
relation_type (string), source_entity (entity name as string), target_entity (entity name as string), confidence (0-1), temporal ({{start_date, end_date, ongoing, date_precision}}), evidence (quote), notes

RULES:
- Use the entity NAME (not ID) for source_entity and target_entity
- Only extract explicit relationships from text
- temporal.date_precision: "exact", "month", "year", "decade", "unknown"
- If no relations found, return empty array

FAMILY RELATION RULES (STRICT):
- SPOUSE_OF: Only extract when text explicitly names BOTH parties as married
  to each other (e.g., "casado con Elena", "esposa de Mario"). The word
  "casado/casada" alone describes marital STATUS, it does NOT identify the spouse.
- CHILD_OF / PARENT_OF: Only when text explicitly names both parent and child
  (e.g., "hijo de Juan García", "madre: Maria López")
- HEIR_OF: Only when text explicitly names both the decedent and the heir
- Never infer family relationships from co-occurrence in a document
- Never infer relationships from entity-level attributes (spouse field, etc.)

Document: {document_id}

ENTITIES:
{entities_json}

TEXT:
{text}

OUTPUT JSON:
{{"relations": [...], "extraction_notes": ""}}"""
    return prompt
