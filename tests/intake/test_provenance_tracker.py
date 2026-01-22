"""Tests for ProvenanceTracker."""

import pytest
from pathlib import Path
from farmer_factory.intake.provenance import ProvenanceTracker


def test_compute_file_hash(tmp_path):
    """Test SHA-256 hash computation."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    tracker = ProvenanceTracker()
    file_hash = tracker._compute_file_hash(test_file)

    # Verify hash format
    assert file_hash.startswith("sha256:")
    assert len(file_hash) == 71  # "sha256:" + 64 hex chars


def test_compute_file_hash_consistency(tmp_path):
    """Test hash is consistent for same content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    tracker = ProvenanceTracker()
    hash1 = tracker._compute_file_hash(test_file)
    hash2 = tracker._compute_file_hash(test_file)

    assert hash1 == hash2
