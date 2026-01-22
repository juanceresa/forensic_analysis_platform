# Preprocessing Module

Document image preprocessing pipeline for OCR and vision model preparation.

## Overview

The `prepare` module implements a two-path preprocessing pipeline:

- **TYPED Path**: For typewritten documents → Binary images for Google Cloud Vision OCR
- **HANDWRITTEN Path**: For handwritten documents → Grayscale images for Claude Vision API

## Architecture

```
Input Image
    ↓
[Triage] ← Determine processing path
    ↓
[Deskew] ← Detect and correct rotation
    ↓
[Denoise] ← Path-specific noise reduction
    ↓
[Enhance] ← Contrast and lighting correction
    ↓
[Binarize] ← TYPED only: convert to black/white
    ↓
ProcessedPage
```

## Usage

```python
from farmer_factory.prepare import PreprocessingPipeline, DocumentPath
import cv2

# Load image
image = cv2.imread("document.png", cv2.IMREAD_GRAYSCALE)

# Process through pipeline
pipeline = PreprocessingPipeline()
result = pipeline.process_page(image)

# Access results
print(f"Path: {result.path}")  # TYPED or HANDWRITTEN
print(f"Skew angle: {result.metadata['skew_angle']}")
print(f"Confidence: {result.metadata['triage_confidence']}")

# Preprocessed image ready for OCR/vision model
preprocessed = result.image
```

## Components

### Triage (`triage.py`)

Routes documents to appropriate processing path based on quality metrics:

- **Text density**: Percentage of image covered by text
- **Line spacing variance**: Regularity indicator (low=typed, high=handwritten)
- **Contrast**: Dynamic range assessment
- **Degradation**: Fading and damage detection

**Decision tree:**
- High line variance (>0.3) → HANDWRITTEN
- Low text density (<0.15) → HANDWRITTEN
- Otherwise → TYPED

### Deskew (`deskew.py`)

Corrects document rotation using Hough line detection:

- Detects horizontal lines in document
- Calculates median skew angle
- Rotates image to straighten (if |angle| > 0.5°)

### Denoise (`denoise.py`)

Path-specific noise reduction:

- **TYPED**: Bilateral filter (edge-preserving smoothing)
- **HANDWRITTEN**: Non-local means (preserves complex textures)

### Enhance (`enhance.py`)

Improves visibility of faded documents:

- **Lighting correction**: Morphological background subtraction
- **CLAHE**: Contrast Limited Adaptive Histogram Equalization

### Binarize (`binarize.py`)

Converts TYPED documents to binary (black text on white background):

- **Sauvola adaptive thresholding**: Handles varying backgrounds

### Pipeline (`pipeline.py`)

Orchestrates all stages and manages data flow:

- `PreprocessingPipeline`: Main pipeline class
- `ProcessedPage`: Result dataclass with image and metadata

## Testing

Run all preprocessing tests:

```bash
pytest tests/prepare/ -v
```

Test coverage:
- Unit tests for each component
- Integration tests for full pipeline
- Edge cases (degraded documents, extreme rotations)

## Implementation Details

### Image Format

All images are processed as NumPy arrays:
- Input: Grayscale `uint8` (0-255)
- Output:
  - TYPED: Binary `uint8` (0 or 255)
  - HANDWRITTEN: Grayscale `uint8` (0-255)

### Processing Time

Typical processing time per page (on standard hardware):
- Triage: ~50ms
- Deskew: ~100ms
- Denoise: ~150ms (bilateral) / ~300ms (NLMeans)
- Enhance: ~120ms
- Binarize: ~80ms

Total: ~500ms (TYPED) / ~650ms (HANDWRITTEN)

### Memory Usage

Peak memory per page:
- Input image: H × W bytes
- Intermediate buffers: ~3× input size
- Output image: H × W bytes

Example: 3000×2000px page ≈ 24MB peak memory

## Dependencies

- `opencv-python` (cv2): Image processing operations
- `numpy`: Array operations
- Standard library: `dataclasses`, `enum`, `typing`

## See Also

- `docs/plans/2026-01-22-prepare-module-design.md`: Design document
- `docs/plans/2026-01-22-prepare-implementation.md`: Implementation plan
- `docs/PREPROCESSING.md`: Original specification
