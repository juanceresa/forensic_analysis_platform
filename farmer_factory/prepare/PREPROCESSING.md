# Farmer House Forensic Intelligence Platform — Preprocessing Pipeline Specification

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.1.0
> **Last Updated:** 2025-01-21
> **Status:** MVP1 Implementation Guide (with triage workflow)

---

## Overview

This document specifies the image preprocessing pipeline for Zone A (The Factory). The pipeline prepares scanned historical documents for OCR, with special handling for:

- Handwritten text (1950s Cuban cursive)
- Typewritten text (period typewriters)
- Mixed documents (typed with handwritten annotations)
- Degraded scans (faded ink, yellowed paper, water damage)

---

## Pipeline Architecture

```
PDF Input → Page Extract → Deskew → Denoise → Enhance → Binarize → Segment → Triage → OCR Ready
```

Each stage is independently configurable and can be bypassed if not needed.

**Key Addition:** Triage stage assesses OCR feasibility and routes documents appropriately.

---

## Document Triage (Stage 0)

Based on Ceresa Archive testing: **Only 34% of documents achieve high OCR quality** (27/80 tested).

### Triage Decision Tree

```
Document → Quick Quality Assessment
              │
              ├─ Text Density >40% → Typed Document Path
              │   └→ Standard preprocessing → OCR
              │
              ├─ Handwritten detected + Good contrast → Handwritten Path
              │   └→ Enhanced preprocessing → Vision Model
              │
              └─ Poor contrast OR illegible → Manual Review Path
                  └→ Flag for human transcription
```

### Quality Assessment Heuristics

```python
# prepare/triage.py

import cv2
import numpy as np
from dataclasses import dataclass
from enum import Enum

class DocumentPath(Enum):
    TYPED = "typed"              # Standard OCR path
    HANDWRITTEN = "handwritten"  # Vision model path
    MANUAL = "manual"            # Human transcription queue

@dataclass
class TriageResult:
    path: DocumentPath
    confidence: float
    reason: str
    estimated_ocr_quality: str  # "excellent", "good", "partial", "poor"

def triage_document(image: np.ndarray) -> TriageResult:
    """
    Assess document and determine processing path.

    Returns:
        TriageResult with recommended path and quality estimate
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Calculate metrics
    text_density = estimate_text_density(gray)
    is_handwritten = detect_handwriting(gray)
    contrast_quality = assess_contrast(gray)
    degradation_score = detect_degradation(gray)

    # Decision logic
    if text_density > 0.40 and not is_handwritten and contrast_quality > 0.7:
        return TriageResult(
            path=DocumentPath.TYPED,
            confidence=0.85,
            reason="High text density, typed text detected, good contrast",
            estimated_ocr_quality="excellent"
        )

    elif is_handwritten and contrast_quality > 0.6 and degradation_score < 0.4:
        return TriageResult(
            path=DocumentPath.HANDWRITTEN,
            confidence=0.75,
            reason="Handwritten text with acceptable quality for vision model",
            estimated_ocr_quality="good"
        )

    else:
        return TriageResult(
            path=DocumentPath.MANUAL,
            confidence=0.90,
            reason=f"Poor quality: contrast={contrast_quality:.2f}, degradation={degradation_score:.2f}",
            estimated_ocr_quality="poor"
        )


def estimate_text_density(gray: np.ndarray) -> float:
    """Estimate percentage of image covered by text."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    text_pixels = np.sum(binary > 0)
    total_pixels = binary.size
    return text_pixels / total_pixels


def detect_handwriting(gray: np.ndarray) -> bool:
    """
    Detect if document contains primarily handwritten text.

    Handwriting indicators:
    - Irregular line spacing
    - Variable stroke width
    - Non-uniform character sizes
    """
    edges = cv2.Canny(gray, 50, 150)

    # Horizontal projection to detect line spacing regularity
    h_projection = np.sum(edges, axis=1)
    peaks = np.where(h_projection > np.mean(h_projection))[0]

    if len(peaks) < 2:
        return False  # Insufficient text

    spacings = np.diff(peaks)
    spacing_variance = np.var(spacings) / (np.mean(spacings) + 1)

    # High variance indicates handwriting
    return spacing_variance > 0.4


def assess_contrast(gray: np.ndarray) -> float:
    """
    Measure document contrast quality.

    Returns:
        0.0-1.0 score (1.0 = excellent contrast)
    """
    # Calculate dynamic range
    min_val, max_val = np.min(gray), np.max(gray)
    dynamic_range = max_val - min_val

    # Normalize to 0-1
    contrast_score = dynamic_range / 255.0

    return contrast_score


def detect_degradation(gray: np.ndarray) -> float:
    """
    Detect document degradation (fading, water damage, etc.)

    Returns:
        0.0-1.0 score (1.0 = severely degraded)
    """
    # Check for fading (low contrast in histogram)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

    # Concentration in middle gray values indicates fading
    middle_range = hist[64:192].sum()
    total = hist.sum()
    middle_concentration = middle_range / total

    # Check for blotches/water damage (high variance in local regions)
    local_vars = []
    h, w = gray.shape
    for y in range(0, h - 50, 50):
        for x in range(0, w - 50, 50):
            region = gray[y:y+50, x:x+50]
            local_vars.append(np.var(region))

    variance_of_variances = np.var(local_vars) if local_vars else 0

    # Combine metrics
    degradation = (middle_concentration + min(variance_of_variances / 10000, 1.0)) / 2

    return degradation
```

### Triage Statistics Tracking

```python
@dataclass
class TriageStats:
    total_documents: int = 0
    typed_path: int = 0
    handwritten_path: int = 0
    manual_path: int = 0

    @property
    def automated_pct(self) -> float:
        """Percentage that can be processed automatically."""
        return (self.typed_path + self.handwritten_path) / self.total_documents if self.total_documents else 0

    def report(self) -> str:
        return f"""
Triage Statistics:
------------------
Total documents:    {self.total_documents}
Typed (OCR):        {self.typed_path} ({self.typed_path/self.total_documents*100:.1f}%)
Handwritten (VM):   {self.handwritten_path} ({self.handwritten_path/self.total_documents*100:.1f}%)
Manual required:    {self.manual_path} ({self.manual_path/self.total_documents*100:.1f}%)

Automation rate:    {self.automated_pct*100:.1f}%
        """
```

---

## Dependencies

```python
# requirements.txt (preprocessing section)
opencv-python>=4.8.0
numpy>=1.24.0
scipy>=1.10.0
PyMuPDF>=1.23.0  # fitz
Pillow>=10.0.0
```

---

## Stage 1: Page Extraction

Extract individual pages from PDF as high-resolution images.

```python
# prepare/page_extract.py

import fitz  # PyMuPDF
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExtractedPage:
    document_id: str
    page_number: int
    image_path: Path
    width: int
    height: int
    dpi: int

def extract_pages(pdf_path: Path, output_dir: Path, dpi: int = 300):
    """Extract all pages from PDF as PNG images at specified DPI."""
    doc = fitz.open(pdf_path)
    document_id = pdf_path.stem
    
    for page_num, page in enumerate(doc):
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        output_path = output_dir / f"{document_id}_page_{page_num:04d}.png"
        pix.save(str(output_path))
        
        yield ExtractedPage(
            document_id=document_id,
            page_number=page_num,
            image_path=output_path,
            width=pix.width,
            height=pix.height,
            dpi=dpi
        )
    doc.close()
```

**Configuration:**
- DPI: 300 (standard for OCR)
- Format: PNG (lossless)
- Color: RGB (preserve for stamp detection)

---

## Stage 2: Deskew

Correct rotation from scanning using Hough line detection.

```python
# prepare/deskew.py

import cv2
import numpy as np

def detect_skew_angle(image: np.ndarray) -> float:
    """Detect skew angle using Hough transform."""
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if angle < -45:
            angle += 90
        elif angle > 45:
            angle -= 90
        angles.append(angle)
    
    return np.median(angles)

def deskew_image(image: np.ndarray, angle: float = None):
    """Rotate image to correct skew."""
    if angle is None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        angle = detect_skew_angle(gray)
    
    if abs(angle) < 0.5:
        return image, 0.0
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), borderValue=(255, 255, 255))
    
    return rotated, angle
```

**Configuration:**
- Min angle threshold: 0.5° (skip smaller corrections)
- Max angle: 45° (beyond this, document may be sideways)
- Background fill: white

---

## Stage 3: Denoise

Remove scanner artifacts while preserving text strokes.

```python
# prepare/denoise.py

import cv2

def denoise_image(image: np.ndarray, method: str = "bilateral"):
    """Remove noise from scanned document."""
    if method == "bilateral":
        # Good for typed text - preserves edges
        return cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
    
    elif method == "nlmeans":
        # Better for handwritten - slower but higher quality
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, h=10, templateWindowSize=7, searchWindowSize=21)
        return cv2.fastNlMeansDenoising(image, h=10)
    
    return image
```

**Configuration:**
- Default: bilateral (fast, good for typed)
- Handwritten: nlmeans (slower, better quality)

---

## Stage 4: Enhance

Improve contrast for OCR, especially for faded documents.

```python
# prepare/enhance.py

import cv2
import numpy as np

def enhance_contrast(image: np.ndarray, method: str = "clahe"):
    """Enhance image contrast for OCR."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    if method == "clahe":
        # Best for uneven lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
    
    elif method == "histogram":
        return cv2.equalizeHist(gray)
    
    return gray

def correct_uneven_lighting(image: np.ndarray):
    """Correct shadows from book spines, etc."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Estimate background
    kernel_size = max(image.shape) // 10
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    
    # Subtract and normalize
    return cv2.divide(gray, background, scale=255)
```

**Configuration:**
- Default: CLAHE (adaptive histogram equalization)
- Clip limit: 2.0
- Tile size: 8x8

---

## Stage 5: Binarize

Convert to black/white for OCR. Critical for handwritten recognition.

```python
# prepare/binarize.py

import cv2
import numpy as np

def binarize_image(image: np.ndarray, method: str = "sauvola"):
    """Convert image to binary (black and white)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    if method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    elif method == "sauvola":
        return sauvola_threshold(gray, window_size=25, k=0.2)
    
    elif method == "adaptive":
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
    return gray

def sauvola_threshold(image: np.ndarray, window_size: int = 25, k: float = 0.2, r: float = 128):
    """Sauvola local adaptive thresholding - best for historical documents."""
    if window_size % 2 == 0:
        window_size += 1
    
    mean = cv2.blur(image.astype(np.float64), (window_size, window_size))
    mean_sq = cv2.blur(image.astype(np.float64) ** 2, (window_size, window_size))
    std = np.sqrt(np.maximum(mean_sq - mean ** 2, 0))
    
    threshold = mean * (1 + k * (std / r - 1))
    binary = np.zeros_like(image)
    binary[image > threshold] = 255
    
    return binary.astype(np.uint8)
```

**Configuration:**
- Default: Sauvola (best for uneven lighting, faded ink)
- Window size: 25 pixels
- k parameter: 0.2

---

## Stage 6: Segment

Detect and classify regions (text, stamps, signatures).

```python
# prepare/segment.py

import cv2
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

class RegionType(Enum):
    TEXT_TYPED = "text_typed"
    TEXT_HANDWRITTEN = "text_handwritten"
    SIGNATURE = "signature"
    STAMP = "stamp"
    MARGINALIA = "marginalia"
    UNKNOWN = "unknown"

@dataclass
class DocumentRegion:
    region_type: RegionType
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    image: np.ndarray = None

def segment_document(image: np.ndarray) -> List[DocumentRegion]:
    """Segment document into classified regions."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Dilate to connect text into blocks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 10))
    dilated = cv2.dilate(binary, kernel, iterations=2)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 50 or h < 20:
            continue
        
        region_image = image[y:y+h, x:x+w]
        region_type, confidence = classify_region(region_image)
        
        regions.append(DocumentRegion(
            region_type=region_type,
            bbox=(x, y, w, h),
            confidence=confidence,
            image=region_image
        ))
    
    regions.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
    return regions

def classify_region(region_image: np.ndarray) -> Tuple[RegionType, float]:
    """Classify region as typed text, handwritten, stamp, etc."""
    h, w = region_image.shape[:2]
    aspect_ratio = w / h if h > 0 else 0
    
    gray = cv2.cvtColor(region_image, cv2.COLOR_BGR2GRAY) if len(region_image.shape) == 3 else region_image
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    fill_density = np.sum(binary > 0) / (w * h)
    
    # Check for color (stamps)
    if len(region_image.shape) == 3:
        hsv = cv2.cvtColor(region_image, cv2.COLOR_BGR2HSV)
        if np.mean(hsv[:, :, 1]) > 30:  # Has saturation
            if 0.5 < aspect_ratio < 2.0:
                return RegionType.STAMP, 0.75
    
    # Signature: wide, low density
    if aspect_ratio > 2.5 and fill_density < 0.2:
        return RegionType.SIGNATURE, 0.70
    
    # Text classification based on line spacing regularity
    edges = cv2.Canny(gray, 50, 150)
    h_proj = np.sum(edges, axis=1)
    peaks = np.where(h_proj > np.mean(h_proj))[0]
    
    if len(peaks) > 1:
        spacings = np.diff(peaks)
        variance = np.var(spacings) / (np.mean(spacings) + 1)
        if variance < 0.3:
            return RegionType.TEXT_TYPED, 0.80
    
    return RegionType.TEXT_HANDWRITTEN, 0.75
```

---

## Pipeline Orchestration

```python
# prepare/pipeline.py

from pathlib import Path
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessedPage:
    document_id: str
    page_number: int
    preprocessed_path: Path
    binary_path: Path
    regions: List[DocumentRegion]
    deskew_angle: float
    triage_result: TriageResult = None

class PreprocessingPipeline:
    def __init__(self, config: dict = None):
        self.config = config or {
            "dpi": 300,
            "triage_enabled": True,
            "deskew_enabled": True,
            "denoise_method": "bilateral",
            "enhance_method": "clahe",
            "binarize_method": "sauvola",
            "segment_enabled": True,
        }
        self.triage_stats = TriageStats()

    def process_document(self, pdf_path: Path, output_dir: Path):
        """Process entire PDF through preprocessing pipeline with triage."""
        output_dir.mkdir(parents=True, exist_ok=True)

        processed_pages = []
        for page in extract_pages(pdf_path, output_dir, self.config["dpi"]):
            image = cv2.imread(str(page.image_path))

            # Triage: Determine processing path
            triage_result = None
            if self.config["triage_enabled"]:
                triage_result = triage_document(image)
                self.triage_stats.total_documents += 1

                if triage_result.path == DocumentPath.MANUAL:
                    self.triage_stats.manual_path += 1
                    logger.warning(
                        f"Page {page.page_number}: {triage_result.reason} - "
                        f"Flagged for manual review"
                    )
                    # Still process but mark for review
                elif triage_result.path == DocumentPath.HANDWRITTEN:
                    self.triage_stats.handwritten_path += 1
                    logger.info(f"Page {page.page_number}: Routing to vision model path")
                else:
                    self.triage_stats.typed_path += 1

            # Deskew
            if self.config["deskew_enabled"]:
                image, angle = deskew_image(image)
            else:
                angle = 0.0

            # Denoise (use stronger denoising for handwritten)
            if triage_result and triage_result.path == DocumentPath.HANDWRITTEN:
                image = denoise_image(image, "nlmeans")
            else:
                image = denoise_image(image, self.config["denoise_method"])

            # Enhance
            image = enhance_contrast(image, self.config["enhance_method"])

            # Save preprocessed
            prep_path = output_dir / f"{page.document_id}_{page.page_number:04d}_prep.png"
            cv2.imwrite(str(prep_path), image)

            # Binarize (skip for handwritten docs going to vision model)
            if triage_result and triage_result.path == DocumentPath.HANDWRITTEN:
                binary = image  # Keep grayscale for vision model
                bin_path = prep_path
            else:
                binary = binarize_image(image, self.config["binarize_method"])
                bin_path = output_dir / f"{page.document_id}_{page.page_number:04d}_bin.png"
                cv2.imwrite(str(bin_path), binary)

            # Segment
            regions = segment_document(image) if self.config["segment_enabled"] else []

            processed_pages.append(ProcessedPage(
                document_id=page.document_id,
                page_number=page.page_number,
                preprocessed_path=prep_path,
                binary_path=bin_path,
                regions=regions,
                deskew_angle=angle,
                triage_result=triage_result,
            ))

            logger.info(
                f"Page {page.page_number}: {len(regions)} regions, "
                f"deskew={angle:.2f}°, path={triage_result.path if triage_result else 'standard'}"
            )

        # Log triage statistics
        if self.config["triage_enabled"]:
            logger.info(self.triage_stats.report())

        return processed_pages
```

---

## Usage

```python
from prepare.pipeline import PreprocessingPipeline
from pathlib import Path

pipeline = PreprocessingPipeline({
    "dpi": 300,
    "denoise_method": "nlmeans",  # Better for handwritten
    "binarize_method": "sauvola",
})

pages = pipeline.process_document(
    pdf_path=Path("documents/deed_1958.pdf"),
    output_dir=Path("output/deed_1958")
)

for page in pages:
    print(f"Page {page.page_number}: {len(page.regions)} regions")
```

---

## Recommended Settings by Document Type

| Document Type | Triage Path | Denoise | Enhance | Binarize | Next Step |
|---------------|-------------|---------|---------|----------|-----------|
| Typed (clean) | TYPED | bilateral | clahe | otsu | Google Cloud Vision OCR |
| Typed (faded) | TYPED | bilateral | clahe | sauvola | Google Cloud Vision OCR |
| Handwritten (good) | HANDWRITTEN | nlmeans | clahe | skip | Claude Vision API |
| Handwritten (poor) | MANUAL | n/a | n/a | n/a | Human transcription |
| Mixed | HANDWRITTEN | nlmeans | clahe | sauvola | Claude Vision API |
| Stamps/Seals | TYPED | none | none | none (keep color) | Region extraction only |

---

## Performance Expectations (Ceresa Archive Baseline)

Based on 80-document test:

| Processing Path | Documents | Success Rate | Avg Time/Doc | Notes |
|----------------|-----------|--------------|--------------|-------|
| Typed OCR | ~100 (34%) | 85-95% | 2 min | High-quality text extraction |
| Vision Model | ~150 (50%) | 70-85% | 5 min | Handwriting interpretation |
| Manual | ~50 (16%) | 100% | 30 min | Human transcriber required |

**Critical Insight:** ~66% of Ceresa Archive requires non-standard OCR approaches. Budget accordingly.

---

*Triage configuration should be tuned after processing 20-30 sample documents from the actual archive. Adjust thresholds based on observed quality distribution.*
