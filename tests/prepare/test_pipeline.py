"""Tests for pipeline module."""

import pytest
import numpy as np
from farmer_factory.prepare.triage import DocumentPath


def test_processed_page_creation():
    """Test ProcessedPage dataclass creation."""
    from farmer_factory.prepare.pipeline import ProcessedPage

    # Create test image
    test_image = np.ones((100, 100), dtype=np.uint8) * 255

    page = ProcessedPage(
        image=test_image,
        path=DocumentPath.TYPED,
        metadata={
            "skew_angle": 2.5,
            "triage_confidence": 0.85,
        }
    )

    assert page.path == DocumentPath.TYPED
    assert page.metadata["skew_angle"] == 2.5
    assert page.image.shape == (100, 100)


def test_preprocessing_pipeline_creation():
    """Test PreprocessingPipeline instantiation."""
    from farmer_factory.prepare.pipeline import PreprocessingPipeline

    pipeline = PreprocessingPipeline()

    # Just check it creates successfully
    assert pipeline is not None
