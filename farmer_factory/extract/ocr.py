"""OCR service for typed documents using Google Cloud Vision API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class TextBlock:
    """Structured text block with position information."""
    text: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # (x, y, width, height)
    block_type: str  # 'paragraph', 'line', 'word'


@dataclass
class OCRResult:
    """Result from OCR extraction."""
    text: str                      # Full extracted text
    confidence: float              # Overall confidence (0.0-1.0)
    page_confidence: float         # Page-level confidence
    blocks: List[TextBlock]        # Structured text blocks with positions
    metadata: Dict[str, Any]       # OCR metadata (language detected, etc.)


class OCRService:
    """Wrapper for Google Cloud Vision API OCR (mocked for testing)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR service.

        Args:
            api_key: Optional Google Cloud Vision API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key
