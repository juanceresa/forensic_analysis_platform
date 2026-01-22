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
