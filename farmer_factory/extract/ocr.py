"""OCR service for typed documents using Google Cloud Vision API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


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

    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from binary image using mocked Google Cloud Vision API.

        Args:
            image: Binary image as numpy array (uint8, 0-255)

        Returns:
            OCRResult with extracted text, confidence, and blocks

        Note:
            This is a MOCKED implementation for testing.
            Real implementation would call Google Cloud Vision API.
        """
        # MOCKED: Simulate OCR extraction
        # In production, this would call Google Cloud Vision API
        logger.warning(
            "⚠️  MOCK OCR - Using simulated text extraction. "
            "Configure GOOGLE_APPLICATION_CREDENTIALS to use real Google Cloud Vision API."
        )

        # Analyze image to determine quality (for confidence calculation)
        # Simple heuristic: more black pixels = more text = higher confidence
        black_pixels = np.sum(image < 128)
        total_pixels = image.size
        text_coverage = black_pixels / total_pixels

        # Base confidence on text coverage (0.15-0.30 typical for documents)
        base_confidence = min(0.95, 0.60 + (text_coverage * 100))

        # Mock extracted text (in real implementation, this would be actual OCR)
        mock_text = "This is mocked OCR text extracted from the document.\n"
        mock_text += "In production, Google Cloud Vision would provide real text.\n"
        mock_text += f"Image size: {image.shape[0]}x{image.shape[1]} pixels"

        # Mock text blocks with positions
        blocks = [
            TextBlock(
                text="This is mocked OCR text extracted from the document.",
                confidence=base_confidence,
                bounding_box=(50, 50, 500, 20),
                block_type="paragraph"
            ),
            TextBlock(
                text="In production, Google Cloud Vision would provide real text.",
                confidence=base_confidence - 0.05,
                bounding_box=(50, 80, 500, 20),
                block_type="paragraph"
            ),
            TextBlock(
                text=f"Image size: {image.shape[0]}x{image.shape[1]} pixels",
                confidence=base_confidence - 0.02,
                bounding_box=(50, 110, 300, 20),
                block_type="line"
            ),
        ]

        # Mock metadata
        metadata = {
            "language": "en",
            "api_version": "mocked_v1",
            "processing_time_ms": 150,
            "image_dimensions": {
                "height": image.shape[0],
                "width": image.shape[1]
            }
        }

        return OCRResult(
            text=mock_text,
            confidence=base_confidence,
            page_confidence=base_confidence - 0.03,
            blocks=blocks,
            metadata=metadata
        )
