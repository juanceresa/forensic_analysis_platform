# Extraction Module

OCR and entity extraction from preprocessed document images.

## Overview

The `extract` module performs OCR and entity extraction on preprocessed documents from the `prepare` module. It implements a two-path architecture optimized for typed and handwritten documents, outputting validated Pydantic models ready for knowledge graph construction.

## Architecture

```
Preprocessed Images (from prepare module)
    ↓
Path Router (based on triage result)
    ↓
┌─────────────────────┬─────────────────────┐
│   TYPED Path        │  HANDWRITTEN Path   │
│                     │                     │
│ Google Cloud Vision │  Claude Vision API  │
│ OCR                 │  (direct on image)  │
│    ↓                │                     │
│ Raw Text            │                     │
│    ↓                │                     │
│ Claude LLM          │                     │
│ (entity extraction  │                     │
│  from text)         │                     │
└─────────────────────┴─────────────────────┘
    ↓
Validated Pydantic Models
(Person, Property, Organization, Location, Document)
    ↓
All entities tagged: verification.tier = TIER_3_AI
    ↓
Structure module (graph building)
```

## Usage

```python
from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import (
    ExtractionPipeline,
    OCRService,
    VisionExtractionService,
    LLMExtractionService,
    SchemaValidator,
)
import cv2

# Initialize pipelines
prep_pipeline = PreprocessingPipeline()
extract_pipeline = ExtractionPipeline(
    ocr_service=OCRService(),
    vision_service=VisionExtractionService(),
    llm_service=LLMExtractionService(),
    validator=SchemaValidator()
)

# Load and preprocess image
raw_image = cv2.imread("document.png", cv2.IMREAD_GRAYSCALE)
preprocessed = prep_pipeline.process_page(raw_image)

# Extract entities
extraction = extract_pipeline.extract_page(preprocessed, document_id="doc_123")

# Access results
print(f"Path: {extraction.path}")
print(f"Entities found: {len(extraction.entities)}")
print(f"Confidence: {extraction.confidence_scores}")

for entity in extraction.entities:
    print(f"- {entity.entity_type}: {entity}")
    print(f"  Verification: {entity.verification.tier} ({entity.verification.confidence:.2f})")
```

## Components

### OCR Service (`ocr.py`)

Wraps Google Cloud Vision API for typed documents.

**Features:**
- Text extraction with confidence scoring
- Structured text blocks with bounding boxes
- Language detection
- Mocked for testing (no real API calls)

**Example:**
```python
from farmer_factory.extract import OCRService

service = OCRService()
result = service.extract_text(binary_image)

print(f"Text: {result.text}")
print(f"Confidence: {result.confidence}")
print(f"Blocks: {len(result.blocks)}")
```

### Vision Extraction Service (`vision.py`)

Wraps Claude Vision API for handwritten documents.

**Features:**
- Direct entity extraction from images
- Handles cursive handwriting and aged documents
- Returns validated Pydantic models
- Mocked for testing

**Example:**
```python
from farmer_factory.extract import VisionExtractionService

service = VisionExtractionService()
result = service.extract_from_image(grayscale_image, document_id="doc_123")

print(f"Entities: {len(result.entities)}")
print(f"Relations: {len(result.relations)}")
print(f"Reasoning: {result.reasoning}")
```

### LLM Extraction Service (`llm.py`)

Wraps Claude text API for entity extraction from OCR text.

**Features:**
- Entity extraction from OCR text
- Combines OCR and LLM confidence scores
- JSON schema-constrained output
- Mocked for testing

**Example:**
```python
from farmer_factory.extract import LLMExtractionService

service = LLMExtractionService()
result = service.extract_from_text(
    text=ocr_text,
    ocr_confidence=0.92,
    document_id="doc_123"
)

print(f"Entities: {len(result.entities)}")
print(f"Combined confidence: {result.confidence}")
```

### Schema Validator (`validator.py`)

Ensures all extracted data conforms to Pydantic schema.

**Features:**
- Validates entities and relations
- Returns partial results (skips invalid items)
- Logs validation errors
- Never fails entire extraction

**Example:**
```python
from farmer_factory.extract import SchemaValidator
from farmer_factory.structure.schema import EntityType

validator = SchemaValidator()
entity = validator.validate_entity(entity_dict, EntityType.PERSON)
```

### Extraction Pipeline (`pipeline.py`)

Orchestrates the two-path extraction process.

**Path Routing:**
- **TYPED path**: OCR → LLM → Validate → TIER_3_AI tagging
- **HANDWRITTEN path**: Vision → Validate → TIER_3_AI tagging

**Confidence Tracking:**
- TYPED: `combined_confidence = min(ocr_confidence, llm_confidence)`
- HANDWRITTEN: `vision_confidence`

## Testing

Run all extraction tests:

```bash
pytest tests/extract/ -v
```

**Test Coverage:**
- Unit tests for each component (OCR, Vision, LLM, Validator)
- Pipeline orchestration tests
- Integration tests (end-to-end with prepare module)
- Module export tests

**Test Files:**
- `test_ocr.py` - OCR service tests
- `test_vision.py` - Vision extraction tests
- `test_llm.py` - LLM extraction tests
- `test_validator.py` - Schema validation tests
- `test_pipeline.py` - Pipeline orchestration tests
- `test_integration.py` - End-to-end tests
- `test_module_exports.py` - Module export tests

## Mocked APIs

All API calls are mocked for testing:
- **Google Cloud Vision**: Returns synthetic OCR results
- **Claude Vision API**: Returns mock entity extractions
- **Claude Text API**: Returns mock entity extractions from text

This enables:
- Fast test execution (no API latency)
- Offline development
- Predictable test behavior
- No API costs during development

## Data Flow

```
Input: ProcessedPage from prepare module
  - image: np.ndarray (binary for TYPED, grayscale for HANDWRITTEN)
  - path: DocumentPath.TYPED or DocumentPath.HANDWRITTEN
  - metadata: preprocessing metadata

Output: ExtractionResult
  - entities: List[BaseEntity] (Person, Property, etc.)
  - relations: List[Relation]
  - confidence_scores: Dict[str, float]
  - path: DocumentPath
  - verification: All entities tagged TIER_3_AI

Next Stage: Structure module
  - Consumes ExtractionResult
  - Builds knowledge graph (NetworkX)
  - Handles entity resolution/merging
```

## Verification Tiers

All extracted entities are tagged with `verification.tier = TIER_3_AI`:

```python
verification = Verification(
    tier=VerificationTier.TIER_3_AI,
    confidence=combined_confidence,
    verified_by=None,
    verified_at=None,
    notes=None
)
```

This indicates:
- **TIER_3_AI**: Unverified AI extraction
- Requires analyst review for promotion to **TIER_2_ANALYST**
- Confidence score tracked for prioritization

## See Also

- `docs/plans/2026-01-22-extract-module-design.md`: Design document
- `docs/plans/2026-01-22-extract-implementation.md`: Implementation plan
- `farmer_factory/prepare/README.md`: Preprocessing pipeline
- `.claude/CLAUDE.md`: Project constraints and legal posture
