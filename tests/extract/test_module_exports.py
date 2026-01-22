"""Test module exports."""

import pytest


def test_module_exports():
    """Test that extract module exports all public classes."""
    from farmer_factory import extract

    # Check all expected exports are available
    assert hasattr(extract, "OCRService")
    assert hasattr(extract, "OCRResult")
    assert hasattr(extract, "VisionExtractionService")
    assert hasattr(extract, "VisionExtractionResult")
    assert hasattr(extract, "LLMExtractionService")
    assert hasattr(extract, "LLMExtractionResult")
    assert hasattr(extract, "ExtractionPipeline")
    assert hasattr(extract, "ExtractionResult")
    assert hasattr(extract, "SchemaValidator")


def test_can_import_directly():
    """Test that classes can be imported directly from extract module."""
    from farmer_factory.extract import (
        OCRService,
        OCRResult,
        VisionExtractionService,
        VisionExtractionResult,
        LLMExtractionService,
        LLMExtractionResult,
        ExtractionPipeline,
        ExtractionResult,
        SchemaValidator,
    )

    # Verify they are the correct classes
    assert OCRService.__name__ == "OCRService"
    assert VisionExtractionService.__name__ == "VisionExtractionService"
    assert LLMExtractionService.__name__ == "LLMExtractionService"
    assert ExtractionPipeline.__name__ == "ExtractionPipeline"
    assert SchemaValidator.__name__ == "SchemaValidator"
