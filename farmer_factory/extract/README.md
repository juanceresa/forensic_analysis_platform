# Extract Module

> **Version:** 1.4.0
> **Last Updated:** 2026-01-27
> **Status:** Zero-shot extraction (domain-aware)

Entity and relation extraction from OCR text using Claude API with domain-specific configuration.

---

## Overview

This module handles:
- OCR text processing (Google Cloud Vision)
- Structured entity extraction (Claude API with zero-shot prompts)
- Relation extraction with domain-configured extraction hints
- Schema validation with Pydantic against domain-defined types
- **Domain-aware processing** - entity/relation types loaded from domain config
- **Zero-shot prompts** - More effective and ~50% cheaper than few-shot

---

## Module Structure

```
extract/
├── models.py              # Pydantic models for extraction schemas
├── api_client.py          # Claude API client with retry logic
├── llm.py                 # LLM extraction service (main interface)
├── parsers.py             # Response parsing and entity transformation
├── chunker.py             # Document text chunking for long documents
├── ocr.py                 # Google Cloud Vision OCR + text normalization
├── vision.py              # Vision API extraction (stub)
├── validator.py           # Schema validation
├── translator.py          # Translation service (GCP Cloud Translation)
├── pipeline.py            # Extraction pipeline orchestration
└── prompts/               # Prompt builders (package)
    ├── __init__.py        # Public exports
    ├── helpers.py         # Domain-aware helper functions
    ├── zero_shot.py       # Zero-shot prompts (default)
    └── few_shot.py        # Few-shot prompts (kept for reference)
```

---

## Components

### 1. Extraction Models (`models.py`)

Pydantic models for structured extraction:

**PersonExtraction:**
- Core: name, alternate_names
- Demographics: birth_date, death_date, nationality, residence, profession, marital_status
- **Family relationships:** mother, father, spouse, children, siblings
- Roles: list of roles in document

**PropertyExtraction:**
- Identity: name, property_type
- Location: location, address, description
- Measurements: area, area_unit
- Registry: registry_number, cadastral_info, folio_number

**OrganizationExtraction:**
- name, org_type, location, address

**LocationExtraction:**
- name, location_type, parent_location, country

### 2. Claude API Client (`api_client.py`)

Handles communication with Anthropic Claude API:

```python
from farmer_factory.extract.api_client import ClaudeAPIClient

client = ClaudeAPIClient(api_key="sk-...")
response = client.call_with_retry(
    prompt="Extract entities from: ...",
    model="claude-sonnet-4-20250514",
    max_retries=3
)
```

**Features:**
- Exponential backoff for rate limits
- Automatic model upgrade on timeout (Haiku → Sonnet)
- Connection error handling
- Configurable retry logic

### 3. LLM Extraction Service (`llm.py`)

Main interface for entity and relation extraction. Uses **zero-shot prompts** by default (more effective and ~50% cheaper than few-shot based on A/B testing).

```python
from farmer_factory.extract import LLMExtractionService

service = LLMExtractionService(api_key="sk-...")

# Extract entities from OCR text
result = service.extract_from_text(
    text="En el año 1958, Don Mario Ceresa...",
    ocr_confidence=0.92,
    document_id="doc_001"
)

# Extract relations between entities
relations = service.extract_relations(
    text="...",
    entities=[person1, person2, property1],
    document_id="doc_001"
)
```

**Methods:**
- `extract_from_text()` - Extract entities with full structured data
- Relation extraction runs after entity extraction and uses the document date
  for temporal fallbacks when needed
- Invalid relation types are skipped without dropping valid relations
- Extraction results are validated via `SchemaValidator` before returning

### 4. Response Parsers (`parsers.py`)

Handles parsing of Claude API responses and transformation to final entities:

```python
from farmer_factory.extract.parsers import (
    parse_entity_response,      # JSON → StructuredEntityExtractionResult
    parse_relation_response,    # JSON → RelationExtractionResult
    transform_to_final_entities,  # Intermediate → BaseEntity list
    transform_to_final_relations, # Intermediate → Relation list
)
```

**Features:**
- Graceful error handling (returns empty results with notes, never raises)
- JSON extraction from markdown code blocks
- Validation against Pydantic models
- Entity name matching for relation linkage (exact, alternate names, fuzzy)

---

## Usage

### Basic Extraction

```python
from farmer_factory.extract import LLMExtractionService
from farmer_factory.config.settings import settings

# Initialize service
service = LLMExtractionService(api_key=settings.anthropic_api_key)

# Extract from OCR text
ocr_text = "En 1958, Mario Ceresa, hijo de Juan Ceresa..."
result = service.extract_from_text(
    text=ocr_text,
    ocr_confidence=0.9,
    document_id="doc_001"
)

# Access extracted entities
for entity in result.entities:
    if isinstance(entity, PersonExtraction):
        print(f"Person: {entity.name}")
        print(f"  Mother: {entity.mother}")
        print(f"  Father: {entity.father}")
```

### With Pipeline

```python
from farmer_factory.extract import ExtractionPipeline, OCRService, LLMExtractionService

pipeline = ExtractionPipeline(
    ocr_service=OCRService(use_real_api=True),
    llm_service=LLMExtractionService(api_key="sk-..."),
)

# Process a preprocessed page
extraction = pipeline.extract_page(
    preprocessed_page=preprocessed,
    document_id="doc_001"
)
```

---

## Domain Configuration

The extraction module is **domain-aware** - it loads entity types, relation types, and extraction hints from the active domain configuration.

### Setting Up Domain

```python
from farmer_factory.domains import domain_registry
from farmer_factory.structure.schema import refresh_type_enums

# Set active domain before extraction
domain_registry.set_active("cuban_property")
refresh_type_enums()

# Now extraction uses domain-specific configuration
service = LLMExtractionService()
```

### Domain-Specific Features

1. **System Context:** Domain-specific context injected into LLM prompts
   - Loaded from `domains/configs/{domain}/prompts/system_context.txt`
   - Provides historical/cultural context for extraction

2. **Extraction Hints:** Per-relation-type keyword hints
   - Configured in `domain.yaml` under `relation_types.*.extraction_hints`
   - Example: `CONFISCATED` has hints like "confiscado", "expropiado"

3. **Temporal vs State Relations:** Different handling for events vs ongoing states
   - Temporal relations (SOLD, CONFISCATED) require dates
   - State relations (OWNS, LOCATED_IN) default to ongoing

### Helper Functions

```python
from farmer_factory.extract.llm import (
    get_temporal_relations,   # Event relations (need dates)
    get_state_relations,      # State relations (dates optional)
    load_system_context,      # Domain-specific LLM context
    get_relation_extraction_hints  # Per-relation keywords
)

# Check temporal relations for current domain
temporal_rels = get_temporal_relations()
# {"SOLD", "BOUGHT", "INHERITED", "CONFISCATED", ...}

state_rels = get_state_relations()
# {"OWNS", "LOCATED_IN", "EMPLOYED_BY", ...}

# Load domain context for prompts
context = load_system_context()
# "You are analyzing historical Cuban property documents..."

# Get extraction hints for relation prompts
hints = get_relation_extraction_hints()
# {"CONFISCATED": ["confiscado", "expropiado", "nacionalizado"], ...}
```

---

## Translation (`translator.py`)

Translates non-English OCR text to English during processing using Google Cloud Translation API (v2).

Free tier: 500k characters/month, then $20/million characters. Uses same GCP credentials as OCR.

### Usage

Translation runs automatically during `process_case()` when `TRANSLATION_ENABLED=true`. Non-English pages are saved to `cases/CASE-ID/ocr_translated/`.

```python
from farmer_factory.extract.translator import translate_text, needs_translation

if needs_translation("es"):
    translated = translate_text(ocr_text, source_language="es")
```

See `docs/guides/ADMIN_GUIDE.md` for setup instructions and model installation.

---

## Prompts

All extraction prompts documented in `PROMPTS.md` in this directory:
- **Prompt 1:** Entity Extraction (Structured Format)
- **Prompt 2:** Relation Extraction (now includes domain-specific hints)

Domain-specific system context is prepended to prompts when available.

See `PROMPTS.md` for complete prompt templates and design rationale.

---

## Testing

```bash
# Unit tests
python -m pytest tests/extract/ -v

# Test specific component
python -m pytest tests/extract/test_llm.py::test_entity_extraction -v
```

---

## Version History

**v1.5.1 (2026-01-28):**
- Removed local Argos/CTranslate2 translation backend (poor quality on legal text)
- GCP Cloud Translation is now the only backend

**v1.5.0 (2026-01-28):**
- Added `translator.py` with GCP Cloud Translation
- Added OCR text normalization (`normalize_ocr_text`) in `ocr.py`
- Translation integrated into processing pipeline with feature flag

**v1.4.0 (2026-01-27):**
- **Zero-shot prompts as default** (more effective and ~50% cheaper)
- Refactored prompts into package (`prompts/`) with helpers, few_shot, zero_shot modules
- Extracted parsing logic to `parsers.py`
- Removed `prompt_mode` parameter (zero-shot only)
- Fixed null coercion bugs for list fields and `TemporalInfo.ongoing`
- Added manifest generation to processing pipeline
- Added `generate-manifest` CLI command for existing cases

**v1.3.0 (2026-01-27):**
- Added domain-aware extraction
- Entity/relation types loaded from domain configuration
- System context injected from domain prompts
- Extraction hints per relation type
- Temporal vs state relation handling

**v1.2.0 (2026-01-25):**
- Refactored into focused modules (models, api_client)
- Removed deprecated ExtractedEntity class
- Added family relationship extraction
- Updated documentation

**v1.1.0 (2026-01-24):**
- Added structured entity extraction
- Replaced simple value/normalized with full schemas

**v1.0.0 (2026-01-22):**
- Initial implementation with Claude API
- Basic entity and relation extraction

---

*For implementation details, see source files in `farmer_factory/extract/`*
