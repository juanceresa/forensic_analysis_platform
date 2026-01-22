"""Preprocessing pipeline orchestration."""

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

from .triage import DocumentPath, triage_document
from .deskew import detect_skew_angle, rotate_image
from .denoise import denoise
from .enhance import enhance_image
from .binarize import sauvola_threshold


@dataclass
class ProcessedPage:
    """Result of preprocessing a document page."""
    image: np.ndarray  # Preprocessed image
    path: DocumentPath  # Processing path used
    metadata: Dict[str, Any]  # Processing metadata (angles, scores, etc.)


class PreprocessingPipeline:
    """
    Preprocessing pipeline for document images.

    Orchestrates triage, deskew, denoise, enhance, and binarize stages.
    """

    def __init__(self):
        """Initialize preprocessing pipeline."""
        pass

    def process_page(self, image: np.ndarray) -> ProcessedPage:
        """
        Process a single document page through the preprocessing pipeline.

        Args:
            image: Grayscale document image (H x W)

        Returns:
            ProcessedPage with preprocessed image and metadata
        """
        metadata: Dict[str, Any] = {}

        # Stage 1: Triage - Determine processing path
        triage_result = triage_document(image)
        path = triage_result.path
        metadata["triage_confidence"] = triage_result.confidence
        metadata["triage_reason"] = triage_result.reason
        metadata.update(triage_result.metrics)

        # Stage 2: Deskew - Detect and correct rotation
        skew_angle = detect_skew_angle(image)
        metadata["skew_angle"] = float(skew_angle)

        if abs(skew_angle) > 0.5:  # Only rotate if significant skew
            image = rotate_image(image, skew_angle)

        # Stage 3: Denoise - Reduce noise based on path
        image = denoise(image, path)

        # Stage 4: Enhance - Improve contrast and lighting
        image = enhance_image(image)

        # Stage 5: Binarize - Convert to black and white (TYPED only)
        if path == DocumentPath.TYPED:
            image = sauvola_threshold(image)
        # HANDWRITTEN stays grayscale for Claude Vision API

        return ProcessedPage(
            image=image,
            path=path,
            metadata=metadata,
        )
