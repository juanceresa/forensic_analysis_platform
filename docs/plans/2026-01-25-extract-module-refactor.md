# Extract Module Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the 1456-line `extract/llm.py` into focused modules for better maintainability and remove deprecated code.

**Architecture:** Extract module currently has all extraction logic in one file. We'll split into:
- `models.py` - Pydantic models for extraction schemas
- `entity_extractor.py` - Entity extraction logic
- `relation_extractor.py` - Relation extraction logic
- `api_client.py` - Claude API communication with retry logic
- `llm.py` - Public API facade (backward compatibility)

**Tech Stack:** Python 3.10+, Pydantic, Anthropic Claude API

**Testing Strategy:** Unit tests exist for extraction logic. We'll ensure imports still work and no functionality breaks during refactor.

---

## Task 1: Create models.py for extraction schemas

**Files:**
- Create: `farmer_factory/extract/models.py`
- Reference: `farmer_factory/extract/llm.py:24-180`

**Step 1: Create models.py with all Pydantic models**

Extract all model definitions from llm.py into new models.py:

```python
"""Pydantic models for LLM extraction results."""

from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class IntermediateEntityType(str, Enum):
    """Entity types from PROMPTS.md extraction schema."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    PROPERTY = "PROPERTY"
    LOCATION = "LOCATION"
    DATE = "DATE"
    MONETARY_VALUE = "MONETARY_VALUE"
    REGISTRY_REFERENCE = "REGISTRY_REFERENCE"


# ============================================================================
# Structured Entity Extraction Models
# ============================================================================

class PersonExtraction(BaseModel):
    """Structured Person entity extraction."""
    entity_type: Literal["PERSON"] = "PERSON"

    # Core identity
    name: str
    alternate_names: List[str] = Field(default_factory=list)

    # Demographics
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    nationality: Optional[str] = None
    residence: Optional[str] = None
    profession: Optional[str] = None
    marital_status: Optional[str] = None

    # Family relationships (names as strings)
    mother: Optional[str] = None
    father: Optional[str] = None
    spouse: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    siblings: List[str] = Field(default_factory=list)

    # Roles
    roles: List[str] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this person")
    notes: Optional[str] = None


class PropertyExtraction(BaseModel):
    """Structured Property entity extraction."""
    entity_type: Literal["PROPERTY"] = "PROPERTY"

    # Identity
    name: Optional[str] = None
    property_type: Optional[str] = None

    # Location & Description
    location: Optional[str] = Field(None, description="Location name (will be linked to Location entity)")
    address: Optional[str] = None
    description: Optional[str] = None

    # Measurements
    area: Optional[float] = None
    area_unit: Optional[str] = None

    # Registry info
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this property")
    notes: Optional[str] = None


class OrganizationExtraction(BaseModel):
    """Structured Organization entity extraction."""
    entity_type: Literal["ORGANIZATION"] = "ORGANIZATION"

    name: str
    org_type: Optional[str] = None
    location: Optional[str] = Field(None, description="Location name (will be linked to Location entity)")
    address: Optional[str] = None

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this organization")
    notes: Optional[str] = None


class LocationExtraction(BaseModel):
    """Structured Location entity extraction."""
    entity_type: Literal["LOCATION"] = "LOCATION"

    name: str
    location_type: Optional[str] = None
    parent_location: Optional[str] = Field(None, description="Parent location name (e.g., 'Camagüey' for 'Florida')")
    country: str = "Cuba"

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str = Field(description="Quote from document mentioning this location")
    notes: Optional[str] = None


# Union type for structured entities
StructuredEntity = PersonExtraction | PropertyExtraction | OrganizationExtraction | LocationExtraction


class StructuredEntityExtractionResult(BaseModel):
    """Result from Claude structured entity extraction."""
    entities: List[StructuredEntity]
    dates: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted dates")
    monetary_values: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted monetary values")
    registry_refs: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted registry references")
    document_date: Optional[str] = None
    document_date_confidence: Optional[float] = None
    extraction_notes: Optional[str] = None


class TemporalInfo(BaseModel):
    """Temporal information for a relation."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ongoing: bool = False
    date_precision: Literal["exact", "month", "year", "decade", "unknown"] = "unknown"


class ExtractedRelation(BaseModel):
    """Single relation extracted from document (intermediate format)."""
    relation_type: str  # Will be validated against RelationType enum
    source_entity: str  # Entity name as string (not ID yet)
    target_entity: str  # Entity name as string (not ID yet)
    confidence: float = Field(ge=0.0, le=1.0)
    temporal: Optional[TemporalInfo] = None
    evidence: str  # Quote from document
    notes: Optional[str] = None


class RelationExtractionResult(BaseModel):
    """Result from Claude relation extraction (intermediate format)."""
    relations: List[ExtractedRelation]
    extraction_notes: Optional[str] = None
```

**Step 2: Verify models.py imports correctly**

Run: `./venv/bin/python -c "from farmer_factory.extract.models import PersonExtraction, StructuredEntityExtractionResult; print('✓ Import successful')"`

Expected: `✓ Import successful`

**Step 3: Commit**

```bash
git add farmer_factory/extract/models.py
git commit -m "refactor(extract): create models.py for extraction schemas

Extracted all Pydantic models from llm.py into dedicated models.py:
- PersonExtraction, PropertyExtraction, OrganizationExtraction, LocationExtraction
- StructuredEntityExtractionResult
- ExtractedRelation, RelationExtractionResult
- TemporalInfo

Part of extract module refactoring to reduce llm.py bloat.
"
```

---

## Task 2: Create api_client.py for Claude API communication

**Files:**
- Create: `farmer_factory/extract/api_client.py`
- Reference: `farmer_factory/extract/llm.py:836-936` (API client methods)

**Step 1: Create api_client.py with Claude API client**

```python
"""Claude API client with retry logic for extraction."""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Wrapper for Anthropic Claude API with retry logic."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (loads from env if None)
        """
        self.api_key = api_key
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or initialize Anthropic client (lazy initialization)."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def call_with_retry(
        self,
        prompt: str,
        model: str = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        api_timeout: int = 120
    ) -> str:
        """
        Call Claude API with exponential backoff retry logic.

        Args:
            prompt: The prompt to send
            model: Model to use (defaults to settings)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            api_timeout: API timeout in seconds

        Returns:
            Claude's response text

        Raises:
            Exception: If all retries fail
        """
        from farmer_factory.config.settings import settings

        if model is None:
            model = settings.claude_model

        client = self._get_client()
        retry_model = settings.claude_model_retry

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Claude API (attempt {attempt + 1}/{max_retries}, model: {model})")

                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=api_timeout
                )

                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    raise ValueError("Empty response from Claude API")

            except Exception as e:
                error_type = type(e).__name__
                logger.warning(f"Claude API error (attempt {attempt + 1}): {error_type}: {str(e)}")

                # Check if we should retry
                is_last_attempt = (attempt == max_retries - 1)

                # Rate limit errors - exponential backoff
                if "rate_limit" in str(e).lower() or "RateLimitError" in error_type:
                    if not is_last_attempt:
                        delay = retry_delay * (2 ** attempt)
                        logger.info(f"Rate limited, waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue

                # Timeout errors - retry with upgrade to Sonnet
                if "timeout" in str(e).lower() or "APITimeoutError" in error_type:
                    if not is_last_attempt and model != retry_model:
                        logger.info(f"Timeout, upgrading to {retry_model} for retry...")
                        model = retry_model
                        time.sleep(retry_delay)
                        continue

                # Connection/server errors - simple retry
                if any(keyword in str(e).lower() for keyword in ["connection", "server", "503", "502", "500"]):
                    if not is_last_attempt:
                        time.sleep(retry_delay)
                        continue

                # If we've exhausted retries or it's a non-retryable error, raise
                if is_last_attempt:
                    logger.error(f"All Claude API retries exhausted: {str(e)}")
                    raise

                # For other errors, just wait and retry
                time.sleep(retry_delay)

        raise Exception("Claude API retries exhausted (should not reach here)")
```

**Step 2: Test API client initialization**

Run: `./venv/bin/python -c "from farmer_factory.extract.api_client import ClaudeAPIClient; client = ClaudeAPIClient(); print('✓ API client created')"`

Expected: `✓ API client created`

**Step 3: Commit**

```bash
git add farmer_factory/extract/api_client.py
git commit -m "refactor(extract): create api_client.py for Claude API communication

Extracted Claude API client with retry logic from llm.py:
- ClaudeAPIClient class with lazy initialization
- Exponential backoff for rate limits
- Model upgrade on timeout (Haiku -> Sonnet)
- Connection error handling

Part of extract module refactoring.
"
```

---

## Task 3: Update llm.py to use new modules and remove deprecated code

**Files:**
- Modify: `farmer_factory/extract/llm.py`

**Step 1: Update imports at top of llm.py**

Replace model definitions (lines 24-180) with imports:

```python
"""LLM extraction service for entity extraction from OCR text using Claude API."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import logging
import json
import uuid

from pydantic import BaseModel, Field

from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.models import (
    IntermediateEntityType,
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntity,
    StructuredEntityExtractionResult,
    TemporalInfo,
    ExtractedRelation,
    RelationExtractionResult
)
from farmer_factory.extract.api_client import ClaudeAPIClient

logger = logging.getLogger(__name__)
```

**Step 2: Remove deprecated ExtractedEntity and EntityExtractionResult**

Delete these classes (they're no longer used):
- `class ExtractedEntity(BaseModel)` (line ~35-42)
- `class EntityExtractionResult(BaseModel)` (line ~143-150)

**Step 3: Update LLMExtractionService to use ClaudeAPIClient**

Replace `_get_client()` and `_call_claude_api_with_retry()` methods with delegation to ClaudeAPIClient:

```python
class LLMExtractionService:
    """Wrapper for Claude text API for entity extraction from OCR text."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key
        self.api_client = ClaudeAPIClient(api_key=api_key)

    # ... rest of methods stay the same ...
```

Replace all calls to `self._call_claude_api_with_retry()` with `self.api_client.call_with_retry()`.

**Step 4: Test that extraction still works**

Run: `./venv/bin/python -c "from farmer_factory.extract.llm import LLMExtractionService; service = LLMExtractionService(); print('✓ LLMExtractionService initialized')"`

Expected: `✓ LLMExtractionService initialized`

**Step 5: Run existing tests**

Run: `./venv/bin/python -m pytest tests/extract/ -v`

Expected: All tests pass

**Step 6: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "refactor(extract): update llm.py to use new modules

Changes:
- Import models from models.py instead of defining inline
- Use ClaudeAPIClient from api_client.py
- Remove deprecated ExtractedEntity and EntityExtractionResult classes
- Delegate API calls to ClaudeAPIClient

Reduced llm.py from 1456 to ~1100 lines.
"
```

---

## Task 4: Update extract/__init__.py exports

**Files:**
- Modify: `farmer_factory/extract/__init__.py`

**Step 1: Add new module exports to __init__.py**

```python
"""Extract module for OCR and LLM-based entity extraction."""

from .ocr import OCRService
from .vision import VisionExtractionService
from .llm import LLMExtractionService
from .validator import SchemaValidator
from .pipeline import ExtractionPipeline

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

__all__ = [
    # Services
    "OCRService",
    "VisionExtractionService",
    "LLMExtractionService",
    "SchemaValidator",
    "ExtractionPipeline",

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
]
```

**Step 2: Test that imports work from extract module**

Run: `./venv/bin/python -c "from farmer_factory.extract import PersonExtraction, ClaudeAPIClient; print('✓ Imports work')"`

Expected: `✓ Imports work`

**Step 3: Test that pipeline still works end-to-end**

Run: `./venv/bin/python -c "from farmer_factory.processing.pipeline import process_case; print('✓ Pipeline imports successfully')"`

Expected: `✓ Pipeline imports successfully`

**Step 4: Commit**

```bash
git add farmer_factory/extract/__init__.py
git commit -m "refactor(extract): update module exports

Added exports for new modules:
- PersonExtraction and other extraction models
- ClaudeAPIClient for direct API access

All public APIs remain backward compatible.
"
```

---

## Task 5: Update documentation

**Files:**
- Modify: `farmer_factory/extract/README.md` (if exists)
- Create: `farmer_factory/extract/README.md` (if doesn't exist)

**Step 1: Create/update extract module README**

```markdown
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
- `extract_relations()` - Extract relations between entities
- Both return validated Pydantic models

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

All extraction prompts defined in `.claude/PROMPTS.md`:
- **Prompt 1:** Entity Extraction (Structured Format)
- **Prompt 2:** Relation Extraction

Prompts are embedded in code but documented externally for review.

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
```

**Step 2: Commit documentation**

```bash
git add farmer_factory/extract/README.md
git commit -m "docs(extract): add module documentation for refactored structure

Documented new module organization:
- models.py for extraction schemas
- api_client.py for Claude API communication
- Updated usage examples
- Version history tracking
"
```

---

## Task 6: Verify end-to-end functionality

**Files:**
- Test: Full pipeline with real/mock data

**Step 1: Run full test suite**

Run: `./venv/bin/python -m pytest tests/ -v`

Expected: All tests pass

**Step 2: Test mock extraction (no API key)**

Run:
```bash
./venv/bin/python -c "
from farmer_factory.extract import LLMExtractionService

service = LLMExtractionService(api_key=None)
result = service.extract_from_text(
    text='Test document with Juan Pérez',
    ocr_confidence=0.9,
    document_id='test_001'
)
print(f'✓ Mock extraction returned {len(result.entities)} entities')
"
```

Expected: `✓ Mock extraction returned N entities`

**Step 3: Verify imports from other modules work**

Run:
```bash
./venv/bin/python -c "
from farmer_factory.processing.pipeline import process_case
from farmer_factory.extract import PersonExtraction, ClaudeAPIClient
print('✓ All imports successful')
"
```

Expected: `✓ All imports successful`

**Step 4: Check line count reduction**

Run: `wc -l farmer_factory/extract/*.py`

Expected: llm.py significantly smaller (~1100 lines vs original 1456)

**Step 5: Final commit**

```bash
git add -A
git commit -m "refactor(extract): complete module refactoring

Summary of changes:
- Split llm.py (1456 lines) into focused modules:
  - models.py: Pydantic extraction schemas (180 lines)
  - api_client.py: Claude API client (120 lines)
  - llm.py: Extraction service (reduced to ~1100 lines)
- Removed deprecated ExtractedEntity and EntityExtractionResult
- Updated module exports and documentation
- All tests passing, backward compatible

Benefits:
- Better separation of concerns
- Easier to maintain and test individual components
- Reduced cognitive load when reading code
"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `farmer_factory/extract/models.py` exists and exports all extraction models
- [ ] `farmer_factory/extract/api_client.py` exists with ClaudeAPIClient
- [ ] `farmer_factory/extract/llm.py` reduced from 1456 to ~1100 lines
- [ ] Deprecated ExtractedEntity and EntityExtractionResult removed
- [ ] All imports updated to use new modules
- [ ] `farmer_factory/extract/__init__.py` exports new modules
- [ ] Documentation updated in extract/README.md
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Mock extraction still works without API key
- [ ] Pipeline integration still works

---

## Rollback Plan

If issues arise:

```bash
# Revert all changes
git log --oneline | head -10  # Find commit before refactoring
git revert <commit-hash>..HEAD

# Or reset if not pushed
git reset --hard <commit-before-refactoring>
```

---

## Notes

**Why this refactoring:**
- llm.py was 1456 lines (hard to navigate)
- Models mixed with API logic
- Deprecated code still present
- Single responsibility principle violated

**What we keep the same:**
- All public APIs (backward compatible)
- Extraction logic and prompts
- Test coverage
- Functionality

**What we improve:**
- Code organization (models, API, extraction separate)
- Maintainability (smaller files)
- Testability (isolated components)
- Documentation (clear module structure)
