"""Preprocessing pipeline orchestration."""

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np

from .triage import DocumentPath


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
