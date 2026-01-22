"""Tests for ManifestManager."""

import pytest
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
