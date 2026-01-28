# LLM Extraction Module Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split 1557-line `llm.py` into focused modules and add zero-shot prompts for cost reduction A/B testing.

**Architecture:** Extract prompts into `prompts/` submodule (few-shot + zero-shot variants), parsing/transformation into `parsers.py`, keeping core service in `llm.py`. Maintain all existing tests and exports.

**Tech Stack:** Python, Pydantic, pytest

**Prompt selection & cost guard:** Choose prompt variant via env/config (e.g., `LLM_PROMPT_MODE=few_shot|zero_shot`), log token usage per call, and enforce a per-request max_tokens cap to prevent runaway costs. Capture quality metrics when toggling modes.

---

## Task 1: Create prompts/helpers.py

**Files:**
- Create: `farmer_factory/extract/prompts/__init__.py`
- Create: `farmer_factory/extract/prompts/helpers.py`

**Step 1: Create prompts directory and __init__.py**

```bash
mkdir -p farmer_factory/extract/prompts
```

Create `farmer_factory/extract/prompts/__init__.py`:

```python
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
```

**Step 2: Create helpers.py with helper functions**

Create `farmer_factory/extract/prompts/helpers.py`:

```python
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
```

**Step 3: Run test to verify helpers work**

Run: `pytest tests/extract/test_llm.py -v -k "test_llm" --tb=short`
Expected: Tests should still pass (using old llm.py for now)

**Step 4: Commit**

```bash
git add farmer_factory/extract/prompts/
git commit -m "refactor: create prompts/helpers.py module"
```

---

## Task 2: Create prompts/few_shot.py

**Files:**
- Create: `farmer_factory/extract/prompts/few_shot.py`

**Step 1: Create few_shot.py with entity prompt builder**

Create `farmer_factory/extract/prompts/few_shot.py`:

```python
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
```

**Step 2: Update prompts/__init__.py to export few_shot functions**

The __init__.py from Task 1 already includes this import.

**Step 3: Commit**

```bash
git add farmer_factory/extract/prompts/few_shot.py
git commit -m "refactor: create prompts/few_shot.py with entity and relation prompts"
```

---

## Task 3: Create prompts/zero_shot.py

**Files:**
- Create: `farmer_factory/extract/prompts/zero_shot.py`
- Modify: `farmer_factory/extract/prompts/__init__.py`

**Step 1: Create zero_shot.py with concise prompts**

Create `farmer_factory/extract/prompts/zero_shot.py`:

```python
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
```

**Step 2: Update prompts/__init__.py to export zero_shot functions**

Edit `farmer_factory/extract/prompts/__init__.py`:

```python
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
    # Few-shot prompts (current)
    "build_entity_prompt",
    "build_relation_prompt",
    # Zero-shot prompts (cost-optimized)
    "build_entity_prompt_zero_shot",
    "build_relation_prompt_zero_shot",
]
```

**Step 3: Commit**

```bash
git add farmer_factory/extract/prompts/
git commit -m "feat: add zero-shot prompts for cost reduction"
```

---

## Task 4: Create parsers.py

**Files:**
- Create: `farmer_factory/extract/parsers.py`

**Step 1: Create parsers.py with response parsing functions**

Create `farmer_factory/extract/parsers.py`:

```python
"""Response parsing and entity transformation for LLM extraction."""

import json
import logging
import uuid
from typing import List, Optional, Tuple

from farmer_factory.extract.models import (
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntityExtractionResult,
    TemporalInfo,
    ExtractedRelation,
    RelationExtractionResult,
)
from farmer_factory.structure.schema import (
    BaseEntity,
    Person,
    Property,
    Organization,
    Location,
    Relation,
    Verification,
    VerificationTier,
    RelationType,
)
from farmer_factory.extract.prompts.helpers import (
    get_temporal_relations,
    get_state_relations,
)

logger = logging.getLogger(__name__)


def parse_entity_response(response_text: str) -> StructuredEntityExtractionResult:
    """
    Parse Claude response into StructuredEntityExtractionResult.

    Handles markdown code blocks and validates JSON schema.

    Args:
        response_text: Raw response from Claude

    Returns:
        Validated StructuredEntityExtractionResult

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        cleaned_text = _extract_json_from_response(response_text)
        data = json.loads(cleaned_text)
        return StructuredEntityExtractionResult(**data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude response: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}...")
        # Retry with code block extraction already attempted; return empty result with warning
        return StructuredEntityExtractionResult(
            entities=[],
            dates=[],
            monetary_values=[],
            registry_refs=[],
            document_date=None,
            document_date_confidence=None,
            extraction_notes=f"JSON parse failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Failed to validate extraction result: {str(e)}")
        return StructuredEntityExtractionResult(
            entities=[],
            dates=[],
            monetary_values=[],
            registry_refs=[],
            document_date=None,
            document_date_confidence=None,
            extraction_notes=f"Schema validation failed: {str(e)}"
        )


def parse_relation_response(response_text: str) -> RelationExtractionResult:
    """
    Parse Claude response into RelationExtractionResult.

    Args:
        response_text: Raw response from Claude

    Returns:
        Validated RelationExtractionResult

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        cleaned_text = _extract_json_from_response(response_text)
        data = json.loads(cleaned_text)
        return RelationExtractionResult(**data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude relation response: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}...")
        return RelationExtractionResult(
            relations=[],
            extraction_notes=f"JSON parse failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Failed to validate relation extraction result: {str(e)}")
        return RelationExtractionResult(
            relations=[],
            extraction_notes=f"Schema validation failed: {str(e)}"
        )


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON from response, handling markdown code blocks."""
    cleaned_text = response_text.strip()

    if "```json" in cleaned_text:
        start = cleaned_text.find("```json") + 7
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()
    elif "```" in cleaned_text:
        start = cleaned_text.find("```") + 3
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()

    return cleaned_text


def transform_to_final_entities(
    extraction: StructuredEntityExtractionResult,
    document_id: str,
    ocr_confidence: float,
) -> List[BaseEntity]:
    """
    Transform structured entities to final schema entities.

    Args:
        extraction: Structured extraction result from Claude
        document_id: Document identifier
        ocr_confidence: OCR confidence score

    Returns:
        List of final entity objects
    """
    final_entities = []

    for entity in extraction.entities:
        combined_confidence = min(ocr_confidence, entity.confidence)

        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=combined_confidence,
            verified_by=None,
            verified_at=None,
            notes=entity.notes,
        )

        short_id = str(uuid.uuid4())[:8]
        entity_id = f"{document_id}_{entity.entity_type.lower()}_{short_id}"
        context_note = f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."

        if isinstance(entity, PersonExtraction):
            person = Person(
                id=entity_id,
                entity_type="PERSON",
                name=entity.name,
                alternate_names=entity.alternate_names,
                birth_date=entity.birth_date,
                death_date=entity.death_date,
                nationality=entity.nationality,
                residence=entity.residence,
                profession=entity.profession,
                marital_status=entity.marital_status,
                mother=entity.mother,
                father=entity.father,
                spouse=entity.spouse,
                children=entity.children,
                siblings=entity.siblings,
                roles=entity.roles,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(person)

        elif isinstance(entity, PropertyExtraction):
            prop = Property(
                id=entity_id,
                entity_type="PROPERTY",
                name=entity.name,
                property_type=entity.property_type,
                address=entity.address,
                description=entity.description,
                area=entity.area,
                area_unit=entity.area_unit,
                registry_number=entity.registry_number,
                cadastral_info=entity.cadastral_info,
                folio_number=entity.folio_number,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(prop)

        elif isinstance(entity, OrganizationExtraction):
            org = Organization(
                id=entity_id,
                entity_type="ORGANIZATION",
                name=entity.name,
                org_type=entity.org_type,
                address=entity.address,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(org)

        elif isinstance(entity, LocationExtraction):
            location = Location(
                id=entity_id,
                entity_type="LOCATION",
                name=entity.name,
                location_type=entity.location_type,
                country=entity.country,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(location)

    logger.info(
        f"Transformed {len(extraction.entities)} structured entities → "
        f"{len(final_entities)} final entities"
    )

    return final_entities


def transform_to_final_relations(
    extraction: RelationExtractionResult,
    entities: List[BaseEntity],
    document_id: str,
    document_date: Optional[str],
    match_entity_func,
) -> List[Relation]:
    """
    Transform intermediate relations to final schema.

    Args:
        extraction: Intermediate extraction result from Claude
        entities: Previously extracted entities
        document_id: Document identifier
        document_date: Document date for temporal fallback
        match_entity_func: Function to match entity names to IDs

    Returns:
        List of final Relation objects
    """
    final_relations = []
    temporal_relations = get_temporal_relations()

    for rel in extraction.relations:
        try:
            relation_type = RelationType(rel.relation_type)
        except ValueError:
            logger.warning(
                f"Skipping relation with invalid type '{rel.relation_type}' "
                f"from {document_id}"
            )
            continue

        source_id = match_entity_func(rel.source_entity, entities)
        target_id = match_entity_func(rel.target_entity, entities)

        if not source_id or not target_id:
            logger.warning(
                f"Skipping relation {rel.relation_type} - "
                f"unmatched entities: {rel.source_entity} -> {rel.target_entity}"
            )
            continue

        temporal_info = apply_temporal_logic(rel, document_date)

        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=rel.confidence,
            verified_by=None,
            verified_at=None,
            notes=rel.notes,
        )

        needs_review = rel.confidence < 0.70 or (
            relation_type.value in temporal_relations
            and temporal_info.date_precision == "unknown"
        )

        final_notes = rel.notes or ""
        if needs_review:
            if rel.confidence < 0.70:
                final_notes += f" Low confidence ({rel.confidence:.2f}) - requires analyst review."
            if (
                relation_type.value in temporal_relations
                and temporal_info.date_precision == "unknown"
            ):
                final_notes += " Missing temporal data for event relation."

        relation = Relation(
            id=f"{document_id}_rel_{uuid.uuid4().hex[:8]}",
            type=relation_type,
            source_id=source_id,
            target_id=target_id,
            verification=verification,
            document_id=document_id,
            evidence=rel.evidence,
            notes=final_notes.strip(),
            date=temporal_info.start_date,
        )

        final_relations.append(relation)

    logger.info(
        f"Transformed {len(extraction.relations)} intermediate relations → "
        f"{len(final_relations)} final relations"
    )

    return final_relations


def apply_temporal_logic(
    relation: ExtractedRelation, document_date: Optional[str]
) -> TemporalInfo:
    """
    Apply smart temporal handling based on relation type.

    Args:
        relation: Extracted relation with temporal info
        document_date: Document date from entity extraction (fallback)

    Returns:
        Enriched TemporalInfo with fallbacks applied
    """
    temporal = relation.temporal or TemporalInfo()
    temporal_relations = get_temporal_relations()
    state_relations = get_state_relations()

    if relation.relation_type in temporal_relations:
        if temporal.start_date:
            return temporal
        elif document_date:
            logger.info(
                f"Using document date as fallback for {relation.relation_type} relation"
            )
            return TemporalInfo(
                start_date=document_date,
                date_precision="year",
                notes="Date inferred from document date",
            )
        else:
            logger.warning(
                f"No temporal data for {relation.relation_type} relation"
            )
            return TemporalInfo(
                date_precision="unknown",
                notes="Missing temporal data for event relation",
            )

    elif relation.relation_type in state_relations:
        if temporal.start_date:
            return temporal
        else:
            return TemporalInfo(date_precision="unknown", ongoing=True)

    return temporal
```

**Step 2: Commit**

```bash
git add farmer_factory/extract/parsers.py
git commit -m "refactor: create parsers.py with response parsing and transformation"
```

---

## Task 5: Refactor llm.py to use new modules

**Files:**
- Modify: `farmer_factory/extract/llm.py`

**Step 1: Replace helper functions with imports**

Edit the top of `farmer_factory/extract/llm.py` to import from new modules and remove the old helper function definitions (lines 37-119):

```python
"""LLM extraction service for entity extraction from OCR text using Claude API."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import logging
import time
import uuid

from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.models import (
    TemporalInfo,
    ExtractedRelation,
)
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.extract.chunker import TextChunker

# Import from new modules
from farmer_factory.extract.prompts import (
    build_entity_prompt,
    build_relation_prompt,
    get_temporal_relations,
    get_state_relations,
)
from farmer_factory.extract.parsers import (
    parse_entity_response,
    parse_relation_response,
    transform_to_final_entities,
    transform_to_final_relations,
    apply_temporal_logic,
)

CHUNK_THRESHOLD = 5000
logger = logging.getLogger(__name__)


@dataclass
class LLMExtractionResult:
    """Result from LLM-based entity extraction."""
    entities: List[BaseEntity]
    relations: List[Relation]
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]
```

**Step 2: Remove old methods from LLMExtractionService**

Remove these methods (they're now in prompts/ or parsers.py):
- `_build_entity_prompt` (use `build_entity_prompt` from prompts)
- `_build_relation_prompt` (use `build_relation_prompt` from prompts)
- `_parse_extraction_response` (use `parse_entity_response` from parsers)
- `_parse_relation_response` (use `parse_relation_response` from parsers)
- `_transform_to_final_entities` (use `transform_to_final_entities` from parsers)
- `_transform_to_final_relations` (use `transform_to_final_relations` from parsers)
- `_apply_temporal_logic` (use `apply_temporal_logic` from parsers)

**Step 3: Update method calls in LLMExtractionService**

Update `_extract_entities` to use new functions:

```python
def _extract_entities(
    self, text: str, ocr_confidence: float, document_id: str
) -> tuple[List[BaseEntity], Optional[str]]:
    """Extract entities from OCR text (first pass)."""
    from farmer_factory.config.settings import settings

    start_time = time.time()

    # Build prompt using new module
    prompt = build_entity_prompt(
        text=text, document_id=document_id, ocr_quality=ocr_confidence
    )

    logger.info(f"Calling Claude API for entity extraction from {document_id}...")
    response_text = self.api_client.call_with_retry(
        prompt=prompt,
        max_retries=settings.max_retries,
        retry_delay=settings.retry_delay,
        api_timeout=settings.api_timeout,
    )

    # Parse response using new module
    extraction = parse_entity_response(response_text)

    # Transform to final entities using new module
    entities = transform_to_final_entities(
        extraction=extraction,
        document_id=document_id,
        ocr_confidence=ocr_confidence,
    )

    return entities, extraction.document_date
```

Update `_extract_relations` similarly:

```python
def _extract_relations(
    self,
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    ocr_confidence: float,
    document_date: Optional[str],
) -> List[Relation]:
    """Extract relations from OCR text using Claude API."""
    from farmer_factory.config.settings import settings

    try:
        start_time = time.time()

        # Build prompt using new module
        prompt = build_relation_prompt(
            text=text, entities=entities, document_id=document_id
        )

        logger.info(
            f"Calling Claude API for relation extraction from {document_id}..."
        )
        response_text = self.api_client.call_with_retry(
            prompt=prompt,
            max_retries=settings.max_retries,
            retry_delay=settings.retry_delay,
            api_timeout=settings.api_timeout,
        )

        # Parse response using new module
        extraction = parse_relation_response(response_text)

        # Transform to final relations using new module
        relations = transform_to_final_relations(
            extraction=extraction,
            entities=entities,
            document_id=document_id,
            document_date=document_date,
            match_entity_func=self._match_entity,
        )

        processing_time = time.time() - start_time
        logger.info(
            f"Relation extraction completed in {processing_time:.2f}s - "
            f"extracted {len(relations)} relations"
        )

        return relations

    except Exception as e:
        logger.error(f"Relation extraction failed for {document_id}: {str(e)}")
        return []
```

**Step 4: Keep these methods in llm.py (core service logic)**

- `__init__`
- `_match_entity`
- `extract_from_text`
- `_extract_entities` (updated)
- `_extract_relations` (updated)
- `_extract_with_chunking`
- `_merge_chunk_entities`
- `_normalize_name_for_matching`
- `_mock_extract`

**Step 5: Run tests to verify refactor**

Run: `pytest tests/extract/test_llm.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "refactor: llm.py uses prompts/ and parsers.py modules"
```

---

## Task 6: Add prompt_mode parameter for A/B testing

**Files:**
- Modify: `farmer_factory/extract/llm.py`

**Step 1: Add prompt_mode to LLMExtractionService**

```python
class LLMExtractionService:
    """Wrapper for Claude text API for entity extraction from OCR text."""

    def __init__(self, api_key: Optional[str] = None, prompt_mode: str = "few_shot"):
        """
        Initialize LLM extraction service.

        Args:
            api_key: Optional Anthropic API key.
            prompt_mode: "few_shot" (default) or "zero_shot" for cost-optimized prompts
        """
        self.api_key = api_key
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self.prompt_mode = prompt_mode

        if prompt_mode not in ("few_shot", "zero_shot"):
            raise ValueError(f"Invalid prompt_mode: {prompt_mode}")
```

**Step 2: Update _extract_entities to use prompt_mode**

```python
def _extract_entities(
    self, text: str, ocr_confidence: float, document_id: str
) -> tuple[List[BaseEntity], Optional[str]]:
    """Extract entities from OCR text (first pass)."""
    from farmer_factory.config.settings import settings
    from farmer_factory.extract.prompts import (
        build_entity_prompt,
        build_entity_prompt_zero_shot,
    )

    # Choose prompt based on mode
    if self.prompt_mode == "zero_shot":
        prompt = build_entity_prompt_zero_shot(
            text=text, document_id=document_id, ocr_quality=ocr_confidence
        )
    else:
        prompt = build_entity_prompt(
            text=text, document_id=document_id, ocr_quality=ocr_confidence
        )

    # ... rest of method unchanged
```

**Step 3: Update _extract_relations similarly**

```python
def _extract_relations(
    self,
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    ocr_confidence: float,
    document_date: Optional[str],
) -> List[Relation]:
    """Extract relations from OCR text using Claude API."""
    from farmer_factory.config.settings import settings
    from farmer_factory.extract.prompts import (
        build_relation_prompt,
        build_relation_prompt_zero_shot,
    )

    try:
        # Choose prompt based on mode
        if self.prompt_mode == "zero_shot":
            prompt = build_relation_prompt_zero_shot(
                text=text, entities=entities, document_id=document_id
            )
        else:
            prompt = build_relation_prompt(
                text=text, entities=entities, document_id=document_id
            )

        # ... rest of method unchanged
```

**Step 4: Update metadata to include prompt_mode**

In `extract_from_text`, update the metadata dict:

```python
metadata = {
    "model": settings.claude_model,
    "api_version": "anthropic_v1",
    "prompt_mode": self.prompt_mode,  # Add this
    "ocr_confidence": ocr_confidence,
    # ... rest unchanged
}
```

**Step 5: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add prompt_mode parameter for few_shot/zero_shot A/B testing"
```

---

## Task 7: Update tests for new structure

**Files:**
- Create: `tests/extract/test_prompts.py`
- Modify: `tests/extract/test_llm.py`

**Step 1: Create test_prompts.py**

Create `tests/extract/test_prompts.py`:

```python
"""Tests for prompt building modules."""

import pytest
from farmer_factory.extract.prompts import (
    build_entity_prompt,
    build_relation_prompt,
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
    ocr_quality_description,
)
from farmer_factory.structure.schema import (
    Person,
    EntityType,
    Verification,
    VerificationTier,
)


class TestHelpers:
    """Test helper functions."""

    def test_ocr_quality_high(self):
        assert "High" in ocr_quality_description(0.95)

    def test_ocr_quality_medium(self):
        assert "Medium" in ocr_quality_description(0.75)

    def test_ocr_quality_low(self):
        assert "Low" in ocr_quality_description(0.55)

    def test_ocr_quality_very_low(self):
        assert "Very Low" in ocr_quality_description(0.3)


class TestFewShotPrompts:
    """Test few-shot prompt builders."""

    def test_entity_prompt_contains_schema(self):
        prompt = build_entity_prompt(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "PERSON ENTITY SCHEMA" in prompt
        assert "PROPERTY ENTITY SCHEMA" in prompt
        assert "entity_type" in prompt

    def test_entity_prompt_contains_document_text(self):
        prompt = build_entity_prompt(
            text="Mario Ceresa owns property",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "Mario Ceresa owns property" in prompt

    def test_relation_prompt_contains_entities(self):
        person = Person(
            id="person_123",
            entity_type=EntityType.PERSON,
            name="Mario Ceresa",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
            extracted_from="test_doc",
        )
        prompt = build_relation_prompt(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        assert "Mario Ceresa" in prompt
        assert "RELATION TYPES" in prompt


class TestZeroShotPrompts:
    """Test zero-shot prompt builders."""

    def test_zero_shot_entity_prompt_is_shorter(self):
        few_shot = build_entity_prompt(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        zero_shot = build_entity_prompt_zero_shot(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        # Zero-shot should be significantly shorter (at least 30% shorter)
        assert len(zero_shot) < len(few_shot) * 0.7

    def test_zero_shot_entity_prompt_contains_essentials(self):
        prompt = build_entity_prompt_zero_shot(
            text="Test document",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "PERSON" in prompt
        assert "PROPERTY" in prompt
        assert "Test document" in prompt
        assert "JSON" in prompt

    def test_zero_shot_relation_prompt_is_shorter(self):
        person = Person(
            id="person_123",
            entity_type=EntityType.PERSON,
            name="Mario Ceresa",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
            extracted_from="test_doc",
        )
        few_shot = build_relation_prompt(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        zero_shot = build_relation_prompt_zero_shot(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        assert len(zero_shot) < len(few_shot) * 0.7
```

**Step 2: Add test for prompt_mode in test_llm.py**

Add to `tests/extract/test_llm.py`:

```python
def test_llm_service_prompt_mode():
    """Test LLMExtractionService supports prompt_mode parameter."""
    # Default is few_shot
    service_default = LLMExtractionService()
    assert service_default.prompt_mode == "few_shot"

    # Explicit few_shot
    service_few = LLMExtractionService(prompt_mode="few_shot")
    assert service_few.prompt_mode == "few_shot"

    # Zero-shot
    service_zero = LLMExtractionService(prompt_mode="zero_shot")
    assert service_zero.prompt_mode == "zero_shot"

    # Invalid mode raises error
    with pytest.raises(ValueError):
        LLMExtractionService(prompt_mode="invalid")
```

**Step 3: Run all tests**

Run: `pytest tests/extract/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/extract/
git commit -m "test: add tests for prompts module and prompt_mode parameter"
```

---

## Task 8: Update golden tests for A/B comparison

**Files:**
- Modify: `tests/golden/test_golden_extraction.py`

**Step 1: Add zero-shot test class**

Add to `tests/golden/test_golden_extraction.py`:

```python
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestZeroShotExtraction:
    """Test zero-shot extraction quality against golden standards."""

    @pytest.fixture
    def service(self):
        return LLMExtractionService(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            prompt_mode="zero_shot"
        )

    def test_escritura_person_recall_zero_shot(self, service):
        """Test zero-shot person recall on escritura."""
        text, expected = load_golden_case("sample_escritura")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura_zero_shot"
        )

        expected_names = get_expected_names(expected, "persons")
        extracted_names = extract_entity_names(result.entities, "PERSON")
        metrics = ExtractionMetrics.calculate(expected_names, extracted_names)

        # Zero-shot threshold may be lower - we're testing cost/quality tradeoff
        assert metrics.recall >= 0.4, (
            f"Zero-shot person recall {metrics.recall:.2f} below threshold. "
            f"Found {metrics.true_positives}/{len(expected_names)}."
        )

    def test_compare_few_shot_vs_zero_shot(self):
        """Compare few-shot vs zero-shot quality and cost."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        text, expected = load_golden_case("sample_escritura")

        # Few-shot extraction
        service_few = LLMExtractionService(api_key=api_key, prompt_mode="few_shot")
        result_few = service_few.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="test_few"
        )
        few_shot_count = len(extract_entity_names(result_few.entities, "PERSON"))

        # Zero-shot extraction
        service_zero = LLMExtractionService(api_key=api_key, prompt_mode="zero_shot")
        result_zero = service_zero.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="test_zero"
        )
        zero_shot_count = len(extract_entity_names(result_zero.entities, "PERSON"))

        print(f"\n=== FEW-SHOT vs ZERO-SHOT COMPARISON ===")
        print(f"Few-shot persons: {few_shot_count}")
        print(f"Zero-shot persons: {zero_shot_count}")
        print(f"Prompt mode in few-shot metadata: {result_few.metadata.get('prompt_mode')}")
        print(f"Prompt mode in zero-shot metadata: {result_zero.metadata.get('prompt_mode')}")

        # Both should extract something
        assert few_shot_count > 0
        assert zero_shot_count > 0
```

**Step 2: Commit**

```bash
git add tests/golden/test_golden_extraction.py
git commit -m "test: add zero-shot vs few-shot A/B comparison tests"
```

---

## Task 9: Update __init__.py exports

**Files:**
- Modify: `farmer_factory/extract/__init__.py`

**Step 1: Add exports for new modules**

Edit `farmer_factory/extract/__init__.py`:

```python
"""
Extraction module.
Handles OCR (Google Cloud Vision) and LLM-based entity/relation extraction (Anthropic Claude).
All extracted data starts at TIER_3_AI verification level.
"""

from .ocr import OCRService, OCRResult
from .vision import VisionExtractionService, VisionExtractionResult
from .llm import LLMExtractionService, LLMExtractionResult
from .pipeline import ExtractionPipeline, ExtractionResult
from .validator import SchemaValidator

# Export models for external use
from .models import (
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntityExtractionResult,
    ExtractedRelation,
    RelationExtractionResult
)

# Export API client for direct use if needed
from .api_client import ClaudeAPIClient

# Export prompt builders for customization
from .prompts import (
    build_entity_prompt,
    build_relation_prompt,
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
)

# Export parsers for testing
from .parsers import (
    parse_entity_response,
    parse_relation_response,
    transform_to_final_entities,
    transform_to_final_relations,
)

__all__ = [
    # Services
    "OCRService",
    "OCRResult",
    "VisionExtractionService",
    "VisionExtractionResult",
    "LLMExtractionService",
    "LLMExtractionResult",
    "ExtractionPipeline",
    "ExtractionResult",
    "SchemaValidator",

    # Models
    "PersonExtraction",
    "PropertyExtraction",
    "OrganizationExtraction",
    "LocationExtraction",
    "StructuredEntityExtractionResult",
    "ExtractedRelation",
    "RelationExtractionResult",

    # API Client
    "ClaudeAPIClient",

    # Prompts
    "build_entity_prompt",
    "build_relation_prompt",
    "build_entity_prompt_zero_shot",
    "build_relation_prompt_zero_shot",

    # Parsers
    "parse_entity_response",
    "parse_relation_response",
    "transform_to_final_entities",
    "transform_to_final_relations",
]
```

**Step 2: Commit**

```bash
git add farmer_factory/extract/__init__.py
git commit -m "refactor: update extract module exports for new structure"
```

---

## Task 10: Fix models.py None coercion bug

**Files:**
- Modify: `farmer_factory/extract/models.py`

**Step 1: Add validator to coerce None to empty list**

This was identified earlier in the session - Claude returns `null` for list fields.

Edit `farmer_factory/extract/models.py` to add the import and validator:

```python
from pydantic import BaseModel, Field, field_validator

# ... existing code ...

class PersonExtraction(BaseModel):
    """Structured Person entity extraction."""
    entity_type: Literal["PERSON"] = "PERSON"

    # Core identity
    name: str
    alternate_names: List[str] = Field(default_factory=list)

    # ... all other fields ...

    @field_validator("alternate_names", "children", "siblings", "roles", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        """Coerce null/None from LLM response to empty list."""
        return v if v is not None else []
```

**Step 2: Run golden tests to verify fix**

Run: `ANTHROPIC_API_KEY=... pytest tests/golden/ -v -s`
Expected: Tests should pass (no validation errors for None lists)

**Step 3: Commit**

```bash
git add farmer_factory/extract/models.py
git commit -m "fix: coerce None to empty list in PersonExtraction model"
```

---

## Task 11: Run full test suite and verify

**Files:** None (verification only)

**Step 1: Run all extract tests**

Run: `pytest tests/extract/ -v`
Expected: All tests pass

**Step 2: Run golden tests**

Run: `ANTHROPIC_API_KEY=... pytest tests/golden/ -v -s`
Expected: Tests pass, quality report prints

**Step 3: Verify line counts**

Run: `wc -l farmer_factory/extract/llm.py farmer_factory/extract/prompts/*.py farmer_factory/extract/parsers.py`

Expected output (approximate):
```
  ~600 farmer_factory/extract/llm.py          (down from 1557)
  ~100 farmer_factory/extract/prompts/__init__.py
  ~100 farmer_factory/extract/prompts/helpers.py
  ~250 farmer_factory/extract/prompts/few_shot.py
  ~150 farmer_factory/extract/prompts/zero_shot.py
  ~300 farmer_factory/extract/parsers.py
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "refactor: complete llm.py split into prompts/ and parsers.py"
```

---

## Tests

- Add parser fallbacks coverage: invalid/partial JSON should return empty results with notes, not raise.
- Verify prompt selection toggles: few-shot vs zero-shot counts, `prompt_mode` metadata, env/flag routing.
- Enforce cost guard: per-request token cap respected and logged (unit + integration with mocked client).
- ID stability/regression: repeated runs produce deterministic IDs when seeded/mocked UUID; relation matching remains stable.

---

## Summary

After completing all tasks:

1. **llm.py** reduced from 1557 → ~600 lines
2. **prompts/** module with few-shot and zero-shot variants
3. **parsers.py** with response parsing and transformation
4. **A/B testing** enabled via `prompt_mode` parameter
5. **Bug fix** for None coercion in list fields
6. **All tests** continue to pass
