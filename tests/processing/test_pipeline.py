"""Integration tests for processing pipeline."""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from farmer_factory.processing.pipeline import process_case
from farmer_factory.processing.exceptions import ProcessingError


def test_process_case_end_to_end(tmp_path):
    """Test full pipeline with real sample PDF."""
    # Setup test case directory
    cases_dir = tmp_path / "cases"
    case_id = "TEST-001"
    case_dir = cases_dir / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)

    # Copy sample PDF
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")
    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    shutil.copy(sample_pdf, intake_dir)

    # Create metadata
    metadata = {
        'id': case_id,
        'name': 'Test Case',
        'family': 'Test',
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create other required directories
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Run processing (with tmp_path as base)
    stats = process_case(case_id, base_dir=cases_dir)

    # Verify statistics returned
    assert stats['documents_processed'] > 0
    assert stats['entities_extracted'] >= 0
    assert stats['entities_merged'] >= 0
    assert stats['relations_added'] >= 0

    # Verify outputs exist
    assert (case_dir / 'output' / 'graph_data.json').exists()
    assert (case_dir / 'processing.log').exists()

    # Verify graph structure
    with open(case_dir / 'output' / 'graph_data.json') as f:
        graph = json.load(f)

    assert 'nodes' in graph
    assert 'links' in graph
    assert 'metadata' in graph
    assert graph['metadata']['case_id'] == case_id


def test_process_case_missing_case_dir(tmp_path):
    """Test error handling when case directory doesn't exist."""
    cases_dir = tmp_path / "cases"

    with pytest.raises(ProcessingError) as exc_info:
        process_case("NONEXISTENT", base_dir=cases_dir)

    assert "not found" in str(exc_info.value).lower()


def test_process_case_no_pdfs(tmp_path):
    """Test handling of case with no PDFs in intake."""
    cases_dir = tmp_path / "cases"
    case_id = "EMPTY-001"
    case_dir = cases_dir / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Should complete successfully but process 0 documents
    stats = process_case(case_id, base_dir=cases_dir)

    assert stats['documents_processed'] == 0
