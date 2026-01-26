# Extract Module

> **Version:** 1.2.0
> **Last Updated:** 2026-01-25
> **Status:** Refactored for maintainability

Entity and relation extraction from OCR text using Claude API.

---

## Overview

This module handles:
- OCR text processing (Google Cloud Vision)
- Structured entity extraction (Claude API with custom prompts)
- Relation extraction between entities
- Schema validation with Pydantic

---

## Module Structure

```
extract/
├── models.py              # Pydantic models for extraction schemas
├── api_client.py          # Claude API client with retry logic
├── llm.py                 # LLM extraction service (main interface)
├── ocr.py                 # Google Cloud Vision OCR
├── vision.py              # Vision API extraction (stub)
├── validator.py           # Schema validation
└── pipeline.py            # Extraction pipeline orchestration
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

Main interface for entity and relation extraction:

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

## Prompts

All extraction prompts documented in `PROMPTS.md` in this directory:
- **Prompt 1:** Entity Extraction (Structured Format)
- **Prompt 2:** Relation Extraction

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
