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
    """Wrapper for Google Cloud Vision API OCR."""

    def __init__(self, use_real_api: bool = False, credentials_path: Optional[str] = None):
        """
        Initialize OCR service.

        Args:
            use_real_api: If True, use real Google Cloud Vision API.
                         If False, use mock data for testing.
            credentials_path: Optional path to service account JSON.
                            If None, uses Application Default Credentials (gcloud auth).
        """
        self.use_real_api = use_real_api
        self.credentials_path = credentials_path
        self.client = None

        if use_real_api:
            try:
                from google.cloud import vision
                import os

                # Use explicit credentials if provided AND file exists
                if credentials_path and os.path.exists(str(credentials_path)):
                    self.client = vision.ImageAnnotatorClient.from_service_account_json(str(credentials_path))
                    logger.info(f"Using Google Cloud Vision with service account: {credentials_path}")
                elif credentials_path:
                    # Credentials path provided but file doesn't exist - warn and use ADC
                    logger.warning(f"Service account file not found: {credentials_path}")
                    logger.info("Falling back to Application Default Credentials")
                    self.client = vision.ImageAnnotatorClient()
                else:
                    # Use Application Default Credentials (gcloud auth)
                    self.client = vision.ImageAnnotatorClient()
                    logger.info("Using Google Cloud Vision with Application Default Credentials")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Vision: {e}")
                logger.warning("Falling back to mock OCR")
                self.use_real_api = False

    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from binary image using Google Cloud Vision API.

        Args:
            image: Binary image as numpy array (uint8, 0-255)

        Returns:
            OCRResult with extracted text, confidence, and blocks
        """
        if self.use_real_api and self.client:
            return self._extract_text_real(image)
        else:
            return self._extract_text_mock(image)

    def _extract_text_real(self, image: np.ndarray) -> OCRResult:
        """Extract text using real Google Cloud Vision API."""
        from google.cloud import vision
        import io

        # Convert numpy array to bytes
        from PIL import Image
        pil_image = Image.fromarray(image)
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        content = img_byte_arr.getvalue()

        # Create Vision API image
        vision_image = vision.Image(content=content)

        # Perform text detection
        response = self.client.document_text_detection(image=vision_image)

        if response.error.message:
            raise Exception(f"Google Cloud Vision API error: {response.error.message}")

        # Extract full text
        full_text = response.full_text_annotation.text if response.full_text_annotation else ""

        # Extract text blocks with confidence
        blocks = []
        total_confidence = 0.0
        block_count = 0

        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                # Get block text
                block_text = ""
                block_confidence = 0.0
                word_count = 0

                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = "".join([symbol.text for symbol in word.symbols])
                        block_text += word_text + " "
                        block_confidence += word.confidence
                        word_count += 1

                if word_count > 0:
                    avg_confidence = block_confidence / word_count
                    total_confidence += avg_confidence
                    block_count += 1

                    # Get bounding box
                    vertices = block.bounding_box.vertices
                    x = vertices[0].x
                    y = vertices[0].y
                    width = vertices[2].x - vertices[0].x
                    height = vertices[2].y - vertices[0].y

                    blocks.append(TextBlock(
                        text=block_text.strip(),
                        confidence=avg_confidence,
                        bounding_box=(x, y, width, height),
                        block_type="paragraph"
                    ))

        # Calculate overall confidence
        overall_confidence = total_confidence / block_count if block_count > 0 else 0.0

        # Metadata
        detected_languages = (
            response.full_text_annotation.pages[0].property.detected_languages
            if (
                response.full_text_annotation.pages
                and response.full_text_annotation.pages[0].property
                and response.full_text_annotation.pages[0].property.detected_languages
            )
            else []
        )
        metadata = {
            "language": (
                detected_languages[0].language_code
                if detected_languages
                else "unknown"
            ),
            "api_version": "google_cloud_vision_v1",
            "image_dimensions": {
                "height": image.shape[0],
                "width": image.shape[1]
            }
        }

        logger.info(f"OCR extracted {len(blocks)} blocks, confidence: {overall_confidence:.2f}")

        return OCRResult(
            text=full_text,
            confidence=overall_confidence,
            page_confidence=overall_confidence,
            blocks=blocks,
            metadata=metadata
        )

    def _extract_text_mock(self, image: np.ndarray) -> OCRResult:
        """Extract text using mock data for testing."""
        logger.warning(
            "⚠️  MOCK OCR - Using simulated text extraction. "
            "Run 'gcloud auth application-default login' to use real Google Cloud Vision API."
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
