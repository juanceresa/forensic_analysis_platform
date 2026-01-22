"""Tests for document triage."""

import pytest
import numpy as np
import cv2
from farmer_factory.prepare.triage import DocumentPath, TriageResult


def test_document_path_enum():
    """Test DocumentPath enum values."""
    assert DocumentPath.TYPED.value == "typed"
    assert DocumentPath.HANDWRITTEN.value == "handwritten"


def test_triage_result_creation():
    """Test TriageResult dataclass creation."""
    result = TriageResult(
        path=DocumentPath.TYPED,
        confidence=0.85,
        reason="High text density, typed text detected",
        metrics={"text_density": 0.52, "line_variance": 0.18}
    )

    assert result.path == DocumentPath.TYPED
    assert result.confidence == 0.85
    assert result.reason == "High text density, typed text detected"
    assert result.metrics["text_density"] == 0.52


def test_estimate_text_density_white_image():
    """Test text density on blank white image."""
    white_image = np.ones((100, 100), dtype=np.uint8) * 255

    from farmer_factory.prepare.triage import estimate_text_density
    density = estimate_text_density(white_image)

    assert density < 0.05  # Almost no text


def test_estimate_text_density_text_image():
    """Test text density on image with text."""
    # Create synthetic text image
    image = np.ones((200, 200), dtype=np.uint8) * 255
    # Add black rectangles simulating text (32% coverage: 80×160 = 12,800 / 40,000)
    image[20:100, 20:180] = 0

    from farmer_factory.prepare.triage import estimate_text_density
    density = estimate_text_density(image)

    assert 0.30 < density < 0.35  # Approximately 32%
