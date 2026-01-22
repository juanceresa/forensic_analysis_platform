"""Tests for ProvenanceTracker."""

import pytest
import json
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


def test_create_provenance_single_file(tmp_path):
    """Test creating provenance for single file."""
    # Create test file
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"PDF content here")

    tracker = ProvenanceTracker()
    provenance = tracker.create_provenance(
        document_id="DOC-001",
        pdf_parts=[test_file],
        page_count=3,
        status="success"
    )

    assert provenance["document_id"] == "DOC-001"
    assert provenance["original_filename"] == "test"
    assert provenance["part_count"] == 1
    assert provenance["total_page_count"] == 3
    assert provenance["status"] == "success"
    assert len(provenance["source_files"]) == 1
    assert provenance["source_files"][0]["filename"] == "test.pdf"
    assert provenance["source_files"][0]["file_hash"].startswith("sha256:")
    assert provenance["source_files"][0]["file_size_bytes"] == 16
    assert "intake_timestamp" in provenance
    assert provenance["extraction_dpi"] == 300


def test_create_provenance_multipart(tmp_path):
    """Test creating provenance for multi-part document."""
    # Create test files
    file1 = tmp_path / "doc.pdf"
    file1.write_bytes(b"Part 1")
    file2 = tmp_path / "doc.1pdf.pdf"
    file2.write_bytes(b"Part 2")

    tracker = ProvenanceTracker()
    provenance = tracker.create_provenance(
        document_id="DOC-002",
        pdf_parts=[file1, file2],
        page_count=5,
        status="success"
    )

    assert provenance["part_count"] == 2
    assert len(provenance["source_files"]) == 2
    assert provenance["source_files"][0]["filename"] == "doc.pdf"
    assert provenance["source_files"][1]["filename"] == "doc.1pdf.pdf"


def test_save_provenance(tmp_path):
    """Test saving provenance to JSON file."""
    provenance = {
        "document_id": "DOC-001",
        "original_filename": "test",
        "status": "success"
    }

    tracker = ProvenanceTracker()
    output_path = tmp_path / "provenance.json"

    tracker.save_provenance(provenance, output_path)

    assert output_path.exists()

    with open(output_path) as f:
        loaded = json.load(f)

    assert loaded["document_id"] == "DOC-001"
    assert loaded["original_filename"] == "test"
