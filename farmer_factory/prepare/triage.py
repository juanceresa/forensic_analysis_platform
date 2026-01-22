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
