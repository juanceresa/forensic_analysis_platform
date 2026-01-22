# Extract Module Design - OCR and Entity Extraction

> **Created:** 2026-01-22
> **Status:** Approved for Implementation
> **Scope:** MVP1 - Two-path extraction with confidence tracking

---

## Overview

The extract module performs OCR and entity extraction on preprocessed document images. It sits between prepare (preprocessed images) and structure (graph building), outputting validated Pydantic models ready for knowledge graph construction.

**Pipeline Flow:**
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

---

## Architecture

### Two-Path Extraction

**TYPED Path:**
- Input: Binary preprocessed images from prepare module
- OCR: Google Cloud Vision API → full text extraction
- Extraction: Claude LLM extracts entities from text
- Output: Pydantic models (Person, Property, etc.)
- Confidence: Combined OCR + LLM confidence scores

**HANDWRITTEN Path:**
- Input: Grayscale preprocessed images from prepare module
- Extraction: Claude Vision API directly on image
- Output: Pydantic models extracted from visual understanding
- Confidence: Vision model confidence scores

### Key Design Decisions

1. **Structured Entity Extraction**: JSON schema-constrained prompts ensure clean, validatable data
2. **Direct Pydantic Models**: No intermediate formats, validate immediately against schema
3. **Confidence-Based Filtering**: Track both API confidence and extraction confidence, flag low-confidence items
4. **TIER_3_AI Tagging**: All extractions start unverified, ready for analyst review
5. **Mocked APIs for Testing**: TDD with fixtures, no real API calls during development

---

## Components

### 1. OCR Service (`ocr.py`)

Wraps Google Cloud Vision API for typed documents.

```python
@dataclass
class OCRResult:
    text: str                    # Full extracted text
    confidence: float            # Overall confidence (0.0-1.0)
    page_confidence: float       # Page-level confidence
    blocks: List[TextBlock]      # Structured text blocks with positions
    metadata: Dict[str, Any]     # OCR metadata (language detected, etc.)

class OCRService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Google Cloud Vision API key."""

    def extract_text(self, image: np.ndarray) -> OCRResult:
        """Extract text from binary image using Google Cloud Vision."""
```

**Features:**
- Batch processing support (multiple pages)
- Confidence scoring per block/word
- Preserve spatial layout (bounding boxes)
- Language detection
- Handles Google Cloud Vision API errors gracefully

**Testing:**
- Mock Google Cloud Vision responses
- Test high/low confidence scenarios
- Test malformed API responses
- Test timeout/retry logic

### 2. Vision Extraction Service (`vision.py`)

Wraps Claude Vision API for handwritten documents.

```python
@dataclass
class VisionExtractionResult:
    entities: List[BaseEntity]   # Extracted entities (Pydantic models)
    relations: List[Relation]    # Extracted relations
    confidence: float            # Overall extraction confidence
    reasoning: str               # Claude's reasoning for extractions
    metadata: Dict[str, Any]     # Vision model metadata

class VisionExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key."""

    def extract_from_image(
        self,
        image: np.ndarray,
        document_id: str
    ) -> VisionExtractionResult:
        """Extract entities directly from handwritten image."""
```

**Features:**
- Structured JSON schema prompting
- Direct entity extraction from visual understanding
- Reasoning capture for audit trail
- Handles cursive handwriting and aged documents
- Validates against Pydantic schema immediately

**Testing:**
- Mock Claude Vision API responses
- Test valid/invalid JSON schema outputs
- Test confidence scoring
- Test Pydantic validation

### 3. LLM Extraction Service (`llm.py`)

Wraps Claude text API for entity extraction from OCR text.

```python
@dataclass
class LLMExtractionResult:
    entities: List[BaseEntity]   # Extracted entities
    relations: List[Relation]    # Extracted relations
    confidence: float            # Extraction confidence
    reasoning: str               # Extraction reasoning
    metadata: Dict[str, Any]

class LLMExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key."""

    def extract_from_text(
        self,
        text: str,
        ocr_confidence: float,
        document_id: str
    ) -> LLMExtractionResult:
        """Extract entities from OCR text."""
```

**Features:**
- Takes OCR confidence into account
- JSON schema-constrained output
- Validates against Pydantic models immediately
- Returns reasoning for transparency
- Handles malformed LLM responses

**Testing:**
- Mock Claude API responses
- Test entity extraction from sample text
- Test confidence calculation
- Test validation error handling

### 4. Schema Validator (`validator.py`)

Ensures all extracted data conforms to the Pydantic schema.

```python
class SchemaValidator:
    """Validates extracted entities against Pydantic models."""

    def validate_entity(
        self,
        entity_dict: Dict[str, Any],
        entity_type: EntityType
    ) -> BaseEntity:
        """
        Validate and instantiate Pydantic model.

        Raises:
            ValidationError: If data doesn't match schema
        """

    def validate_extraction(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> Tuple[List[BaseEntity], List[Relation]]:
        """Validate entire extraction batch."""
```

**Validation Strategy:**
- Parse LLM/Vision JSON responses immediately
- Catch Pydantic ValidationErrors with detailed messages
- Log validation failures for debugging
- Return partial results (valid entities only) + error report
- Never fail entire extraction due to single malformed entity

**Testing:**
- Test valid entity dictionaries
- Test invalid/malformed data
- Test partial validation (some valid, some invalid)
- Test all entity types (Person, Property, etc.)

### 5. Extraction Pipeline (`pipeline.py`)

Orchestrates the two-path extraction process.

```python
@dataclass
class ExtractionResult:
    """Complete extraction result for a document page."""
    entities: List[BaseEntity]      # All extracted entities
    relations: List[Relation]       # All extracted relations
    ocr_result: Optional[OCRResult] # OCR output (TYPED path only)
    confidence_scores: Dict[str, float]  # Multi-level confidence tracking
    path: DocumentPath              # Which path was used
    processing_metadata: Dict[str, Any]

class ExtractionPipeline:
    def __init__(
        self,
        ocr_service: OCRService,
        vision_service: VisionExtractionService,
        llm_service: LLMExtractionService,
        validator: SchemaValidator
    ):
        """Initialize extraction pipeline with services."""

    def extract_page(
        self,
        processed_page: ProcessedPage,  # From prepare module
        document_id: str
    ) -> ExtractionResult:
        """Extract entities from preprocessed page."""
```

**Pipeline Logic:**

TYPED path:
1. OCR → extract text with confidence
2. LLM → extract entities from text
3. Validate → ensure schema compliance
4. Tag → set verification.tier = TIER_3_AI
5. Return → ExtractionResult with combined confidence

HANDWRITTEN path:
1. Vision → extract entities directly from image
2. Validate → ensure schema compliance
3. Tag → set verification.tier = TIER_3_AI
4. Return → ExtractionResult with vision confidence

**Confidence Tracking:**

TYPED path:
- `ocr_confidence`: Google Cloud Vision confidence
- `llm_confidence`: Claude extraction confidence
- `combined_confidence`: min(ocr_confidence, llm_confidence)

HANDWRITTEN path:
- `vision_confidence`: Claude Vision API confidence

All entities get:
```python
verification = Verification(
    tier=VerificationTier.TIER_3_AI,
    confidence=combined_confidence,
    verified_by=None,
    verified_at=None,
    notes=None
)
```

**Testing:**
- Test TYPED path with mocked OCR + LLM
- Test HANDWRITTEN path with mocked Vision API
- Test confidence calculation
- Test TIER_3_AI tagging
- Test error recovery

---

## Error Handling

### Error Recovery Strategies

```python
@dataclass
class ExtractionError:
    error_type: str              # ocr_failure, llm_timeout, validation_error
    message: str
    page_number: Optional[int]
    recovery_action: str         # What was done to recover

class ExtractionPipeline:
    def extract_page(self, ...) -> ExtractionResult:
        """Extract with error recovery."""
        try:
            # Normal extraction flow
        except OCRError as e:
            # Log error, return empty result with error metadata
        except LLMTimeoutError as e:
            # Retry with exponential backoff
        except ValidationError as e:
            # Return partial results, log invalid entities
```

**Recovery Actions:**
- **OCR failures**: Return empty text, flag for manual review, log error
- **LLM timeouts**: Retry up to 3 times with exponential backoff
- **Validation errors**: Skip invalid entities, keep valid ones, log issues
- **API rate limits**: Queue and retry with delays
- **Malformed responses**: Log for debugging, return partial results

---

## Prompts

Extraction prompts stored separately following CLAUDE.md guidance:

```
farmer_factory/extract/prompts/
├── typed_extraction.txt      # LLM prompt for typed documents
├── handwritten_vision.txt    # Vision prompt for handwritten docs
└── schema_definitions.json   # JSON schema for structured output
```

**Prompt Requirements:**
- Include JSON schema definitions inline
- Explicitly instruct: "Never make legal conclusions"
- Request reasoning/confidence for transparency
- Handle entity types: Person, Property, Organization, Location, Document
- Request relations between entities
- Specify verification tier (TIER_3_AI) in output

**Example Prompt Structure:**
```
You are extracting entities from Cuban property documents for forensic analysis.

Extract the following entity types:
- Person (name, dates, roles)
- Property (location, area, registry info)
- Organization (banks, courts, government)
- Location (cities, provinces)
- Document (type, date, issuer)

Also extract relations between entities (ownership, inheritance, witnessing, etc.).

Output as JSON matching this schema:
{schema_definitions}

CRITICAL: Never make legal conclusions. Only extract factual information as stated in the document.

Provide your reasoning and confidence (0.0-1.0) for each entity.
```

---

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

---

## Testing Strategy

### Test Coverage

```
tests/extract/
├── test_ocr.py              # OCR service unit tests
├── test_vision.py           # Vision extraction unit tests
├── test_llm.py              # LLM extraction unit tests
├── test_validator.py        # Schema validation tests
├── test_pipeline.py         # Pipeline orchestration tests
└── test_integration.py      # End-to-end extraction tests
```

### Test Fixtures

**Mock API Responses:**
- `fixtures/google_vision_response.json` - Sample OCR output
- `fixtures/claude_vision_response.json` - Sample vision extraction
- `fixtures/claude_llm_response.json` - Sample text extraction
- `fixtures/preprocessed_images/` - Sample images from prepare module

**Expected Outputs:**
- `fixtures/expected_entities.json` - Sample entity extractions
- `fixtures/expected_relations.json` - Sample relation extractions

### Unit Tests

- Mock all API calls (no real API usage)
- Test confidence calculation logic
- Validate Pydantic model instantiation
- Test error recovery paths
- Verify TIER_3_AI tagging
- Test partial extraction (some entities invalid)

### Integration Tests

- Test TYPED path: preprocessed binary image → entities
- Test HANDWRITTEN path: preprocessed grayscale → entities
- Test confidence thresholds and filtering
- Test multi-page document processing
- Test end-to-end with prepare module output

---

## Module Exports

```python
# farmer_factory/extract/__init__.py
"""
Extraction module.
Handles OCR (Google Cloud Vision) and LLM-based entity/relation extraction.
All extracted data starts at TIER_3_AI verification level.
"""

from .ocr import OCRService, OCRResult
from .vision import VisionExtractionService, VisionExtractionResult
from .llm import LLMExtractionService, LLMExtractionResult
from .pipeline import ExtractionPipeline, ExtractionResult
from .validator import SchemaValidator

__all__ = [
    "OCRService",
    "OCRResult",
    "VisionExtractionService",
    "VisionExtractionResult",
    "LLMExtractionService",
    "LLMExtractionResult",
    "ExtractionPipeline",
    "ExtractionResult",
    "SchemaValidator",
]
```

---

## Usage Example

```python
from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import ExtractionPipeline, OCRService, VisionExtractionService, LLMExtractionService
import cv2

# Initialize pipelines
prep_pipeline = PreprocessingPipeline()
extract_pipeline = ExtractionPipeline(
    ocr_service=OCRService(),  # Uses mocked API for testing
    vision_service=VisionExtractionService(),
    llm_service=LLMExtractionService()
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

---

## Implementation Notes

### API Configuration (Future)

When ready for real API usage, configure in `.env`:
```
GOOGLE_CLOUD_VISION_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

Services will load from environment:
```python
class OCRService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
```

### Development Approach

1. **TDD with Mocks**: All tests use mocked API responses
2. **Fast Iteration**: No API calls = fast test execution
3. **Predictable**: Fixtures ensure consistent test behavior
4. **Cost-Free**: No API charges during development
5. **Offline-Capable**: Can develop without internet

### Dependencies

New dependencies for extract module:
- `google-cloud-vision` - Google Cloud Vision API client
- `anthropic` - Anthropic Claude API client (already in project)
- Existing: `pydantic`, `numpy`, `opencv-python`

---

## See Also

- `docs/plans/2026-01-22-extract-implementation.md`: Implementation plan
- `docs/plans/2026-01-22-schema-design.md`: Entity schema specification
- `docs/plans/2026-01-22-prepare-module-design.md`: Preprocessing pipeline
- `.claude/CLAUDE.md`: Project constraints and legal posture
