"""Unit tests for processing exceptions."""

import pytest
from farmer_factory.processing.exceptions import ProcessingError


def test_processing_error_basic():
    """Test ProcessingError can be raised and caught."""
    with pytest.raises(ProcessingError) as exc_info:
        raise ProcessingError("Test error message")

    assert str(exc_info.value) == "Test error message"


def test_processing_error_with_context():
    """Test ProcessingError with contextual information."""
    document_id = "test_doc_page_0"
    stage = "preprocessing"

    error_msg = f"Failed {stage} for {document_id}: Image corrupted"

    with pytest.raises(ProcessingError) as exc_info:
        raise ProcessingError(error_msg)

    assert document_id in str(exc_info.value)
    assert stage in str(exc_info.value)


def test_processing_error_inherits_exception():
    """Test ProcessingError is a proper Exception."""
    error = ProcessingError("Test")
    assert isinstance(error, Exception)
