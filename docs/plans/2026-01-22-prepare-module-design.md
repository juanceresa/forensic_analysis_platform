# Prepare Module Design - Preprocessing Pipeline

> **Created:** 2026-01-22
> **Status:** Approved for Implementation
> **Scope:** MVP1 - TYPED and HANDWRITTEN paths with degradation detection

---

## Overview

The prepare module transforms raw page images from intake into OCR-ready outputs. It sits between intake (PDF → PNG extraction) and extract (OCR/LLM processing).

**Pipeline Flow:**
```
Intake (raw PNGs at 300 DPI)
    ↓
Triage → Routes to TYPED or HANDWRITTEN path
    ↓
Preprocessing Pipeline:
  - Deskew (rotation correction)
  - Denoise (noise removal, path-specific)
  - Enhance (contrast/lighting, degradation-aware)
  - Binarize (black/white conversion, TYPED only)
    ↓
Output (OCR-ready images) → Extract module
```

---

## Architecture

### Two Processing Paths

**TYPED Path:**
- Clean or faded typewritten documents
- Target: Google Cloud Vision OCR
- Output: Binary (black/white) images
- Optimized for: Edge detection, clean text boundaries

**HANDWRITTEN Path:**
- Cursive handwriting (1950s Cuban documents)
- Target: Claude Vision API
- Output: Grayscale (preserve tonal information)
- Optimized for: Stroke preservation, texture retention

### Key Decisions

1. **Degradation-aware**: Detects fading and adjusts enhancement automatically
2. **Path-specific processing**: Different denoise/binarize for typed vs handwritten
3. **Configurable stages**: Each stage can be tuned or disabled per document type
4. **Quality tracking**: Log metrics for threshold tuning after sample processing

---

## Triage Stage

### Purpose

Analyze raw images and route to appropriate processing path based on document characteristics.

### TriageResult Data Structure

```python
from dataclasses import dataclass
from enum import Enum

class DocumentPath(Enum):
    TYPED = "typed"
    HANDWRITTEN = "handwritten"

@dataclass
class TriageResult:
    path: DocumentPath
    confidence: float  # 0.0-1.0
    reason: str  # Human-readable explanation
    metrics: dict  # {text_density, line_variance, contrast, degradation}
```

### Quality Metrics

**1. Text Density**
- Percentage of image covered by text
- Method: Otsu thresholding
- Range: 0.0-1.0
- Typical typed: 0.4-0.6
- Typical handwritten: 0.2-0.5

**2. Line Spacing Variance**
- Regularity of horizontal text lines
- Method: Horizontal projection analysis
- High variance (>0.4) = handwritten
- Low variance (<0.3) = typed

**3. Contrast Score**
- Dynamic range of image
- Method: (max_pixel - min_pixel) / 255
- Range: 0.0-1.0
- Good contrast: >0.7
- Poor contrast: <0.5

**4. Degradation Score**
- Fading and damage detection
- Method: Histogram middle-range concentration + local variance analysis
- Range: 0.0-1.0 (higher = worse)
- Faded documents: >0.5
- Clean documents: <0.3

### Routing Logic

```
IF text_density > 0.40 AND line_variance < 0.3 AND contrast > 0.7:
    → TYPED (clean typed document, confidence: 0.85)

ELSE IF text_density > 0.40 AND line_variance < 0.3 AND degradation > 0.5:
    → TYPED (faded typed document, confidence: 0.75)

ELSE IF line_variance > 0.4:
    → HANDWRITTEN (detected irregular spacing, confidence: 0.80)

ELSE:
    → TYPED (default fallback, confidence: 0.60, log warning)
```

**Note:** No MANUAL path in MVP1 - process everything but flag low-confidence cases for review.

---

## Preprocessing Stages

### Stage 1: Deskew

**Purpose:** Correct rotation from scanning errors.

**Method:** Hough line detection
- Detect dominant line angles in image
- Calculate median angle
- Rotate image to align text horizontally

**Configuration:**
- Min angle threshold: 0.5° (skip smaller corrections)
- Max angle: 45° (beyond this may indicate sideways document)
- Background fill: white (255, 255, 255)

**Output:** Rotated image + deskew angle (for logging)

---

### Stage 2: Denoise

**Purpose:** Remove scanner artifacts while preserving text strokes.

**TYPED Path:**
- Method: Bilateral filter
- Parameters: d=9, sigmaColor=75, sigmaSpace=75
- Fast, preserves sharp edges (typed characters)

**HANDWRITTEN Path:**
- Method: Non-local means denoising
- Parameters: h=10, templateWindowSize=7, searchWindowSize=21
- Slower but better quality for continuous strokes (cursive)

**Output:** Denoised grayscale image

---

### Stage 3: Enhance

**Purpose:** Improve contrast for OCR, especially for faded documents.

**Clean Documents (degradation < 0.5):**
- Method: CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Parameters: clipLimit=2.0, tileGridSize=(8, 8)
- Handles uneven lighting

**Faded Documents (degradation ≥ 0.5):**
- Method: CLAHE + uneven lighting correction
- First: Estimate and subtract background
- Then: Apply CLAHE to normalized image
- Critical for yellowed paper and faded ink

**Output:** Enhanced grayscale image

---

### Stage 4: Binarize

**Purpose:** Convert to black/white for OCR engines.

**TYPED Path:**
- Method: Sauvola adaptive thresholding
- Parameters: window_size=25, k=0.2, r=128
- Best for uneven lighting and faded text
- Output: Binary image (0 or 255 values)

**HANDWRITTEN Path:**
- **Skip binarization** - keep enhanced grayscale
- Vision models need full tonal range for stroke interpretation
- Output: Enhanced grayscale from Stage 3

---

## Pipeline Orchestration

### PreprocessingPipeline Class

```python
class PreprocessingPipeline:
    """Orchestrates document preprocessing with triage and path-specific processing."""

    def __init__(self, config: dict = None):
        """
        Initialize pipeline with configuration.

        Default config:
        - dpi: 300 (matches intake module)
        - deskew_enabled: True
        - denoise_typed: "bilateral"
        - denoise_handwritten: "nlmeans"
        - enhance_method: "clahe"
        - binarize_method: "sauvola"
        - degradation_threshold: 0.5
        """

    def process_page(self, image_path: Path, output_dir: Path) -> ProcessedPage:
        """
        Process single page through pipeline.

        Steps:
        1. Load image (from intake output)
        2. Triage (determine TYPED or HANDWRITTEN)
        3. Deskew (rotation correction)
        4. Denoise (path-specific method)
        5. Enhance (degradation-aware)
        6. Binarize (TYPED only)
        7. Save outputs (prep + binary)
        8. Return ProcessedPage with metadata
        """
```

### ProcessedPage Data Structure

```python
@dataclass
class ProcessedPage:
    document_id: str
    page_number: int
    preprocessed_path: Path  # Grayscale enhanced image
    binary_path: Optional[Path]  # Binary image (TYPED only, None for HANDWRITTEN)
    triage_result: TriageResult
    deskew_angle: float
    processing_time: float  # Seconds, for performance tracking
```

### Batch Processing

Process all pages from intake module's output directory:
- Maintain sequential page numbering
- Preserve document_id from intake
- Create parallel output structure
- Generate batch summary with triage distribution

---

## Output Structure

```
output/CASE-001/
├── intake/
│   ├── manifest.json
│   ├── provenance/
│   └── raw_images/
│       └── DOC-001/
│           ├── page_001.png  ← Input
│           ├── page_002.png
│           └── ...
└── preprocessed/
    ├── DOC-001/
    │   ├── page_001_prep.png     ← Enhanced grayscale
    │   ├── page_001_bin.png      ← Binary (if TYPED)
    │   ├── page_001_metadata.json ← Triage + metrics
    │   ├── page_002_prep.png
    │   ├── page_002_bin.png
    │   └── ...
    └── preprocessing_summary.json  ← Batch statistics
```

### Metadata JSON Schema

```json
{
  "document_id": "DOC-001",
  "page_number": 1,
  "triage": {
    "path": "TYPED",
    "confidence": 0.85,
    "reason": "High text density, typed text detected, good contrast",
    "metrics": {
      "text_density": 0.52,
      "line_variance": 0.18,
      "contrast": 0.78,
      "degradation": 0.35
    }
  },
  "deskew_angle": -1.2,
  "processing_time": 2.3,
  "timestamp": "2026-01-22T14:30:00.123456Z"
}
```

### Preprocessing Summary Schema

```json
{
  "case_id": "CASE-001",
  "total_pages": 45,
  "triage_distribution": {
    "TYPED": 28,
    "HANDWRITTEN": 17
  },
  "average_metrics": {
    "degradation": 0.42,
    "contrast": 0.71,
    "deskew_angle": 0.8
  },
  "processing_time_total": 124.5,
  "timestamp": "2026-01-22T14:35:00.123456Z"
}
```

---

## Error Handling

### Recoverable Errors

**Corrupted image file:**
- Skip page
- Log error with page number
- Continue processing remaining pages
- Mark as failed in summary

**Triage failure (metrics calculation error):**
- Default to TYPED path
- Set confidence to 0.5
- Log warning
- Continue processing

**Deskew failure (no lines detected):**
- Skip rotation (use original orientation)
- Set deskew_angle to 0.0
- Log warning
- Continue processing

**Enhancement/Binarization failure:**
- Use previous stage output
- Log warning
- Continue processing

### Unrecoverable Errors

**Output directory write failure:**
- Raise exception immediately
- Do not continue processing
- Clear partial outputs

**OpenCV library error:**
- Log full traceback
- Raise exception
- Report which stage failed

---

## Logging Strategy

### Log Levels

**INFO:**
- Page processing start/complete
- Triage decisions with confidence
- Deskew angles
- Processing time per page

**WARNING:**
- Low confidence triage (<0.7)
- High degradation detected (>0.6)
- Stage failures (with fallback)
- Abnormal deskew angles (>10°)

**ERROR:**
- Corrupted images
- Unrecoverable processing failures
- Write errors

### Example Log Output

```
INFO: Processing page DOC-001/page_001.png
INFO: Triage: TYPED (confidence=0.85) - High text density, good contrast
INFO: Deskew: Corrected -1.2° rotation
INFO: Completed page_001 in 2.3s
WARNING: Processing page DOC-001/page_015.png
WARNING: High degradation detected (0.67) - applying enhanced preprocessing
INFO: Triage: TYPED (confidence=0.75) - Faded typed document
```

---

## Metrics Tracking

Track statistics for threshold tuning:

**Per-batch metrics:**
- Triage distribution (TYPED %, HANDWRITTEN %)
- Average degradation score
- Average contrast score
- Average deskew angle
- Processing time per page
- Failure rate by stage

**Purpose:** After processing 20-30 sample documents, analyze metrics to tune:
- Triage thresholds (text_density, line_variance cutoffs)
- Degradation threshold (when to apply enhanced processing)
- Enhancement parameters (CLAHE clip limit, tile size)

---

## Testing Strategy

### Unit Tests (Per Component)

**Triage:**
- Text density calculation accuracy
- Line variance calculation
- Contrast score calculation
- Degradation detection
- Routing logic for edge cases

**Deskew:**
- Angle detection accuracy (test with rotated images)
- Rotation quality
- Skip logic for small angles

**Denoise:**
- Noise reduction effectiveness
- Edge preservation (typed text)
- Stroke preservation (handwritten text)

**Enhance:**
- Contrast improvement
- Degradation handling
- Uneven lighting correction

**Binarize:**
- Sauvola threshold accuracy
- Handling faded text
- Handling uneven lighting

### Integration Tests

**Full pipeline scenarios:**
- Clean typed document → TYPED path → binary output
- Faded typed document → TYPED path with degradation handling
- Handwritten document → HANDWRITTEN path → grayscale output
- Batch processing multiple pages with mixed types

### Test Fixtures

Create synthetic test images:
- Rotated images (various angles)
- Noisy images (salt-and-pepper noise)
- Faded images (low contrast)
- Handwritten text samples (irregular spacing)
- Mixed documents (typed + handwritten)

---

## Dependencies

All dependencies already in requirements.txt:

```python
opencv-python>=4.9.0
numpy>=1.26.0
scipy>=1.11.0
Pillow>=10.1.0
PyMuPDF>=1.23.0  # For potential PDF re-reading if needed
```

---

## Implementation Notes

1. **Start with clean typed documents** - Verify pipeline works before tackling faded/handwritten
2. **Test triage thresholds** - Initial values from spec, but expect to tune after real data
3. **Log everything** - Metrics are critical for tuning
4. **Keep stages independent** - Each stage should work in isolation for testing
5. **Optimize later** - Correctness first, performance second (batch processing is acceptable for MVP1)

---

## Success Criteria

**Functional:**
- Process TYPED documents to binary images suitable for OCR
- Process HANDWRITTEN documents to grayscale suitable for vision models
- Correctly triage >80% of documents on first pass
- Handle faded documents with enhanced preprocessing

**Quality:**
- All unit tests passing
- Integration test with sample documents
- Triage metrics logged for tuning
- Error handling for common failure modes

**Performance:**
- Process one page in <5 seconds (acceptable for MVP1)
- Batch processing with progress logging
- Graceful handling of large batches (100+ pages)

---

*Ready for implementation with TDD approach following brainstorming → plan → test → implement cycle.*
