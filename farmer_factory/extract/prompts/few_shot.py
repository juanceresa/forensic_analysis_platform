"""Few-shot prompt templates with examples (current approach)."""

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


def build_entity_prompt(
    text: str,
    document_id: str,
    document_type: str = "unknown",
    ocr_quality: float = 0.0,
) -> str:
    """
    Build few-shot entity extraction prompt with examples.

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

    prompt = f"""{context_section}You are a forensic document analyst extracting entities from historical Cuban property documents. Extract factual information only — never make legal conclusions.

Analyze the following OCR text and extract all entities with their detailed attributes.

ENTITY TYPES:
1. PERSON - Extract biographical and family relationship data
2. PROPERTY - Extract property details
3. ORGANIZATION - Extract organization details
4. LOCATION - Extract geographic information
5. DATE - Dates mentioned in document (returned separately)
6. MONETARY_VALUE - Financial amounts (returned separately)
7. REGISTRY_REFERENCE - Registry references (returned separately)

PERSON ENTITY SCHEMA:
{{
  "entity_type": "PERSON",
  "name": "Mario Ceresa",  // Required: Full name as written in document
  "alternate_names": ["Don Mario Ceresa", "M. Ceresa"],  // Optional: Titles, abbreviations

  // Demographics (extract if mentioned):
  "birth_date": "1920" or "1920-03-15",  // Year or full date
  "death_date": null,
  "nationality": "Cuban",
  "residence": "Miramar, Havana",  // Where they live
  "profession": "industrialist",
  "marital_status": "married" or "casado/casada",

  // Family relationships (CRITICAL - extract if mentioned):
  "mother": "María López de Queral",  // Mother's name
  "father": "Juan Ceresa",  // Father's name
  "spouse": "Rosa Queral",  // Spouse name (use primary if multiple)
  "children": ["Mario Ceresa Jr.", "Rosa Ceresa"],  // List of children's names
  "siblings": ["Carlos Ceresa"],  // List of siblings' names

  // Roles (what they're doing in this document):
  "roles": ["owner", "seller"],  // e.g., owner, buyer, seller, witness, notary

  // Extraction metadata:
  "confidence": 0.95,  // 0.0-1.0 based on OCR clarity
  "context": "...comparece Don Mario Ceresa, hijo de Juan Ceresa y María López...",
  "notes": "Family relationships mentioned in preamble"
}}

IMPORTANT - Family Relationships:
- Look for phrases like "hijo de" (son of), "hija de" (daughter of)
- "casado con" (married to), "esposa de" (wife of), "esposo de" (husband of)
- "hermano de" (brother of), "hermana de" (sister of)
- Extract EXACTLY as written, preserve Spanish names completely
- If only partial info (e.g., just father mentioned), that's fine
- Don't invent relationships not stated in the text

PROPERTY ENTITY SCHEMA:
{{
  "entity_type": "PROPERTY",
  "name": "Central Santa Maria",  // Property name
  "property_type": "sugar mill" or "ingenio",  // Type: finca, ingenio, central, hacienda
  "location": "Florida, Camagüey",  // Location as text (will be linked later)
  "address": "Carretera Central Km 15",
  "description": "Sugar mill with 500 hectares",
  "area": 500.0,
  "area_unit": "hectares" or "caballerías",
  "registry_number": "Folio 123, Tomo V",
  "cadastral_info": "Finca 456",
  "folio_number": "123",
  "confidence": 0.90,
  "context": "...la finca Central Santa Maria...",
  "notes": "Area mentioned in cadastral description"
}}

ORGANIZATION ENTITY SCHEMA:
{{
  "entity_type": "ORGANIZATION",
  "name": "Banco Núñez",
  "org_type": "bank" or "banco",
  "location": "Havana",
  "address": "Calle Obispo 305",
  "confidence": 0.85,
  "context": "...el Banco Núñez...",
  "notes": null
}}

LOCATION ENTITY SCHEMA:
{{
  "entity_type": "LOCATION",
  "name": "Florida",
  "location_type": "municipality" or "municipio",
  "parent_location": "Camagüey",  // Parent location (e.g., province)
  "country": "Cuba",
  "confidence": 0.95,
  "context": "...en el municipio de Florida...",
  "notes": null
}}

OCR QUALITY CONSIDERATIONS:
- If text is unclear, lower confidence score and note in "notes"
- Common OCR errors in Spanish: ñ→n, á→a, rn→m, ll→U
- Handwritten text may have lower confidence

EXTRACTION RULES:
- Extract only what the document explicitly states
- Preserve original Spanish terms and names
- If a field is not mentioned, use null or empty list []
- For PERSON entities, family relationships are HIGH PRIORITY
- Don't guess or infer data not in the text

DOCUMENT METADATA:
Document ID: {document_id}
Document Type: {document_type}
OCR Quality: {quality_desc} ({ocr_quality:.2f})
Language: Spanish

OCR TEXT:
{text}

Respond with JSON in this format:
{{
  "entities": [
    // Array of PERSON, PROPERTY, ORGANIZATION, LOCATION entities
  ],
  "dates": [
    // Dates found: {{"value": "15 de marzo de 1958", "normalized": "1958-03-15", "context": "..."}}
  ],
  "monetary_values": [
    // Money amounts: {{"value": "$50,000 pesos", "normalized": {{"amount": 50000, "currency": "pesos"}}, "context": "..."}}
  ],
  "registry_refs": [
    // Registry references: {{"value": "Folio 123", "normalized": "Folio 123, Tomo V", "context": "..."}}
  ],
  "document_date": "1958-03-15",  // Main document date
  "document_date_confidence": 0.90,
  "extraction_notes": "Overall good OCR quality. Family relationships extracted from preamble."
}}"""
    return prompt


def build_relation_prompt(
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    document_type: str = "unknown",
) -> str:
    """
    Build few-shot relation extraction prompt with examples.

    Args:
        text: OCR-extracted text
        entities: Previously extracted entities
        document_id: Document identifier
        document_type: Type of document

    Returns:
        Formatted prompt string
    """
    # Build entities JSON for prompt
    entities_list = []
    for entity in entities:
        entities_list.append(
            {
                "id": entity.id,
                "type": entity.entity_type,
                "name": getattr(entity, "name", str(entity.id)),
            }
        )

    entities_json = json.dumps(entities_list, indent=2, ensure_ascii=False)

    system_context = load_system_context()
    context_section = f"\n{system_context}\n" if system_context else ""

    # Build relation types section from domain config
    relation_hints = get_relation_extraction_hints()
    if domain_registry.is_active and relation_hints:
        relation_types_section = "RELATION TYPES:\n"
        for rel_type, config in domain_registry.active.relation_types.items():
            hints_str = ""
            if config.extraction_hints:
                hints_str = f" (look for: {', '.join(config.extraction_hints[:3])})"
            relation_types_section += (
                f"- {rel_type}: {config.description}{hints_str}\n"
            )
    else:
        relation_types_section = """RELATION TYPES:
- OWNS: Person/Organization owns Property (current or historical)
- SOLD: Person sold Property to another Person (transaction)
- BOUGHT: Person bought Property from another Person
- INHERITED: Person inherited Property (from another Person)
- CONFISCATED: Government/Organization confiscated Property
- WITNESSED: Person witnessed a transaction or legal act
- NOTARIZED: Notary certified a document
- REGISTERED_IN: Property registered in a Registry
- LOCATED_IN: Property/Person located in a Location
- EMPLOYED_BY: Person employed by Organization
- RELATED_TO: Family relationship between Persons
"""

    prompt = f"""{context_section}You are a forensic document analyst extracting relationships from historical Cuban property documents. Extract factual relationships only — never make legal conclusions about claim validity.

Analyze the OCR text and the previously extracted entities to identify relationships between them.

For each relationship, provide:
1. relation_type: One of the defined types below
2. source_entity: The entity at the start of the relationship
3. target_entity: The entity at the end of the relationship
4. confidence: 0.0-1.0 based on textual evidence
5. temporal: Date or date range if applicable
6. evidence: Quote from document supporting this relationship
7. notes: Observations, caveats, or ambiguities

{relation_types_section}
TEMPORAL INFORMATION:
- Extract start_date and end_date where applicable
- For ongoing relationships, set ongoing: true
- Use date_precision: "exact", "month", "year", "decade", or "unknown"

CRITICAL: Only extract relationships explicitly stated or directly implied by the document. Do not infer relationships that require outside knowledge.

DOCUMENT METADATA:
Document ID: {document_id}
Document Type: {document_type}

EXTRACTED ENTITIES:
{entities_json}

OCR TEXT:
{text}

REQUIRED OUTPUT FORMAT:
You MUST respond with a valid JSON object in the format shown below.
- If you find relations, include them in the "relations" array
- If you find NO relations, return an empty array: "relations": []
- ALWAYS return valid JSON - never return prose explanations
- Use "extraction_notes" to explain why no relations were found

Example response with relations:
{{
  "relations": [
    {{
      "relation_type": "OWNS",
      "source_entity": "Mario Ceresa",
      "target_entity": "Central Santa Maria",
      "confidence": 0.88,
      "temporal": {{
        "start_date": "1945-01-01",
        "end_date": null,
        "ongoing": true,
        "date_precision": "year"
      }},
      "evidence": "...Don Mario Ceresa, propietario del Central Santa Maria...",
      "notes": "Ownership stated but acquisition date not specified in this document"
    }}
  ],
  "extraction_notes": "Document is a notarial certification of ownership."
}}

Example response with NO relations:
{{
  "relations": [],
  "extraction_notes": "Document is a loan fee notification with no property ownership or transaction relationships."
}}"""
    return prompt
