"""Tests for document triage."""

import pytest
import numpy as np
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
