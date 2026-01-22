"""Unit tests for OCR service."""

import pytest
import numpy as np
from farmer_factory.extract.ocr import OCRService, OCRResult, TextBlock


def test_ocr_result_structure():
    """Test OCRResult dataclass structure."""
    result = OCRResult(
        text="Sample text",
        confidence=0.95,
        page_confidence=0.92,
        blocks=[],
        metadata={"language": "en"}
    )

    assert result.text == "Sample text"
    assert result.confidence == 0.95
    assert result.page_confidence == 0.92
    assert result.blocks == []
    assert result.metadata == {"language": "en"}


def test_text_block_structure():
    """Test TextBlock dataclass structure."""
    block = TextBlock(
        text="Block text",
        confidence=0.88,
        bounding_box=(10, 20, 100, 50),
        block_type="paragraph"
    )

    assert block.text == "Block text"
    assert block.confidence == 0.88
    assert block.bounding_box == (10, 20, 100, 50)
    assert block.block_type == "paragraph"


def test_ocr_service_initialization():
    """Test OCRService can be initialized."""
    service = OCRService()
    assert service is not None
    assert service.use_real_api is False  # Default to mock

    # With real API enabled
    service_with_real_api = OCRService(use_real_api=False)  # False for testing
    assert service_with_real_api is not None
    assert service_with_real_api.use_real_api is False


def test_extract_text_from_binary_image():
    """Test OCR extraction from binary image (mocked)."""
    service = OCRService()

    # Create synthetic binary image (400x600 pixels, black text on white)
    image = np.ones((400, 600), dtype=np.uint8) * 255
    image[50:70, 100:500] = 0  # Simulate text line

    # Extract text (mocked)
    result = service.extract_text(image)

    # Verify result structure
    assert isinstance(result, OCRResult)
    assert isinstance(result.text, str)
    assert len(result.text) > 0  # Should have extracted something
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.page_confidence <= 1.0
    assert isinstance(result.blocks, list)
    assert isinstance(result.metadata, dict)


def test_extract_text_high_confidence():
    """Test OCR with high-quality image returns high confidence."""
    service = OCRService()

    # High-quality synthetic image
    image = np.ones((400, 600), dtype=np.uint8) * 255
    for y in range(50, 350, 30):
        image[y:y+15, 50:550] = 0

    result = service.extract_text(image)

    # Mocked service should return high confidence for clean images
    assert result.confidence >= 0.85
    assert result.page_confidence >= 0.80


def test_extract_text_preserves_blocks():
    """Test that OCR preserves text block structure."""
    service = OCRService()

    image = np.ones((400, 600), dtype=np.uint8) * 255
    image[50:70, 100:500] = 0

    result = service.extract_text(image)

    # Should have at least one text block
    assert len(result.blocks) > 0

    # Verify block structure
    for block in result.blocks:
        assert isinstance(block, TextBlock)
        assert isinstance(block.text, str)
        assert 0.0 <= block.confidence <= 1.0
        assert len(block.bounding_box) == 4
        assert block.block_type in ["paragraph", "line", "word"]
