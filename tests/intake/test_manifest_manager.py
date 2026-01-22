"""Tests for ManifestManager."""

import pytest
import json
from datetime import datetime
from farmer_factory.intake.manifest import ManifestManager


def test_manifest_manager_init():
    """Test ManifestManager initialization."""
    manifest = ManifestManager(case_id="CASE-001")

    assert manifest.case_id == "CASE-001"
    assert len(manifest.documents) == 0
    assert isinstance(manifest.intake_timestamp, datetime)


def test_add_document_success():
    """Test adding successful document to manifest."""
    manifest = ManifestManager(case_id="CASE-001")

    manifest.add_document(
        document_id="DOC-001",
        filename="test document",
        status="success",
        part_count=2,
        page_count=5
    )

    assert len(manifest.documents) == 1
    doc = manifest.documents[0]
    assert doc["document_id"] == "DOC-001"
    assert doc["filename"] == "test document"
    assert doc["status"] == "success"
    assert doc["part_count"] == 2
    assert doc["page_count"] == 5
    assert "error" not in doc


def test_add_document_failed():
    """Test adding failed document to manifest."""
    manifest = ManifestManager(case_id="CASE-001")

    manifest.add_document(
        document_id="DOC-002",
        filename="corrupted",
        status="failed",
        part_count=0,
        page_count=0,
        error="PDF corrupted"
    )

    assert len(manifest.documents) == 1
    doc = manifest.documents[0]
    assert doc["status"] == "failed"
    assert doc["error"] == "PDF corrupted"


def test_get_summary():
    """Test manifest summary calculation."""
    manifest = ManifestManager(case_id="CASE-001")

    manifest.add_document("DOC-001", "doc1", "success", 1, 3)
    manifest.add_document("DOC-002", "doc2", "success", 2, 5)
    manifest.add_document("DOC-003", "doc3", "failed", 0, 0, error="corrupted")

    summary = manifest.get_summary()

    assert summary["total_documents"] == 3
    assert summary["successful"] == 2
    assert summary["failed"] == 1
    assert summary["skipped"] == 0


def test_save_manifest(tmp_path):
    """Test saving manifest to JSON file."""
    manifest = ManifestManager(case_id="CASE-001")
    manifest.add_document("DOC-001", "doc1", "success", 1, 3)

    output_path = tmp_path / "manifest.json"
    manifest.save_manifest(output_path)

    assert output_path.exists()

    with open(output_path) as f:
        loaded = json.load(f)

    assert loaded["case_id"] == "CASE-001"
    assert loaded["total_documents"] == 1
    assert loaded["successful"] == 1
    assert loaded["failed"] == 0
    assert len(loaded["documents"]) == 1
    assert "intake_timestamp" in loaded
