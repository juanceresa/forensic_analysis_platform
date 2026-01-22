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
