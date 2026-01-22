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

    # With API key
    service_with_key = OCRService(api_key="test_key")
    assert service_with_key is not None
