"""Document triage for routing to appropriate processing path."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any
import cv2
import numpy as np


class DocumentPath(Enum):
    """Processing path for document."""
    TYPED = "typed"
    HANDWRITTEN = "handwritten"


@dataclass
class TriageResult:
    """Result of document triage."""
    path: DocumentPath
    confidence: float  # 0.0-1.0
    reason: str
    metrics: Dict[str, Any]


def estimate_text_density(image: np.ndarray) -> float:
    """
    Estimate percentage of image covered by text.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Text density (0.0-1.0)
    """
    # Apply Otsu's thresholding (inverted - text becomes white)
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Count text pixels (white after inversion)
    text_pixels = np.sum(binary > 0)
    total_pixels = binary.size

    return text_pixels / total_pixels if total_pixels > 0 else 0.0


def estimate_line_spacing_variance(image: np.ndarray) -> float:
    """
    Calculate coefficient of variation for line spacing.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Variance score (0.0-1.0+, where low = regular, high = irregular)
    """
    # Binarize image
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Sum horizontally to get row densities
    row_densities = np.sum(binary, axis=1) / 255

    # Find rows with significant text (peaks)
    threshold = np.mean(row_densities) + np.std(row_densities)
    text_rows = np.where(row_densities > threshold)[0]

    if len(text_rows) < 2:
        return 0.0  # Not enough lines to measure variance

    # Calculate gaps between consecutive text rows
    gaps = np.diff(text_rows)

    # Filter out very small gaps (within same line)
    significant_gaps = gaps[gaps > 5]

    if len(significant_gaps) < 2:
        return 0.0

    # Coefficient of variation: std / mean
    mean_gap = np.mean(significant_gaps)
    std_gap = np.std(significant_gaps)

    return std_gap / mean_gap if mean_gap > 0 else 0.0


def estimate_contrast(image: np.ndarray) -> float:
    """
    Calculate contrast score based on dynamic range.

    Args:
        image: Grayscale image (H x W)

    Returns:
        Contrast score (0.0-1.0, where 1.0 = full range)
    """
    min_val = np.min(image)
    max_val = np.max(image)

    dynamic_range = max_val - min_val

    return dynamic_range / 255.0


def estimate_degradation(image: np.ndarray) -> float:
    """
    Estimate degradation level (fading, stains, damage).

    Args:
        image: Grayscale image (H x W)

    Returns:
        Degradation score (0.0-1.0, where 0.0 = clean, 1.0 = severely degraded)
    """
    # Calculate histogram
    hist = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()

    # Normalize histogram
    hist = hist / hist.sum()

    # Calculate mean intensity
    mean_intensity = np.mean(image)

    # Degradation indicators:
    # 1. Low mean intensity (faded)
    fading_score = 1.0 - (mean_intensity / 255.0)

    # 2. Histogram spread (noise/artifacts)
    # Use entropy as a measure of randomness
    # Clean documents have concentrated histograms
    hist_nonzero = hist[hist > 0]
    entropy = -np.sum(hist_nonzero * np.log2(hist_nonzero))
    # Normalize entropy (max is 8.0 for uniform distribution over 256 bins)
    noise_score = entropy / 8.0

    # Combine scores (weighted average)
    degradation = 0.7 * fading_score + 0.3 * noise_score

    return np.clip(degradation, 0.0, 1.0)


def triage_document(image: np.ndarray) -> TriageResult:
    """
    Triage document to appropriate processing path.

    Args:
        image: Grayscale image (H x W)

    Returns:
        TriageResult with path, confidence, reason, and metrics
    """
    # Calculate all metrics
    text_density = estimate_text_density(image)
    line_variance = estimate_line_spacing_variance(image)
    contrast = estimate_contrast(image)
    degradation = estimate_degradation(image)

    metrics = {
        "text_density": text_density,
        "line_variance": line_variance,
        "contrast": contrast,
        "degradation": degradation,
    }

    # Routing logic
    # TYPED: High text density, low line variance (regular spacing)
    # HANDWRITTEN: Lower density OR high line variance (irregular)

    # Decision tree:
    # 1. High line variance (> 0.3) → HANDWRITTEN
    # 2. Low text density (< 0.15) → HANDWRITTEN (sparse writing)
    # 3. Otherwise → TYPED

    if line_variance > 0.3:
        # High variance = handwritten
        confidence = min(line_variance, 0.95)
        reason = f"High line spacing variance ({line_variance:.2f}) indicates handwriting"
        path = DocumentPath.HANDWRITTEN
    elif text_density < 0.15:
        # Low density = likely handwritten (sparse)
        confidence = 0.7
        reason = f"Low text density ({text_density:.2f}) suggests handwriting"
        path = DocumentPath.HANDWRITTEN
    else:
        # Regular spacing, sufficient density = typed
        confidence = min(text_density, 0.95)
        reason = f"Regular spacing and text density ({text_density:.2f}) indicate typed text"
        path = DocumentPath.TYPED

    return TriageResult(
        path=path,
        confidence=confidence,
        reason=reason,
        metrics=metrics,
    )
