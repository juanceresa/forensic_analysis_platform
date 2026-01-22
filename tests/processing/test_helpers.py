"""Unit tests for processing helper functions."""

import pytest
from pathlib import Path
from farmer_factory.processing.helpers import load_pdf_pages


def test_load_pdf_pages_single_page(tmp_path):
    """Test PDF to image conversion with single page PDF."""
    # Note: This test requires a real PDF file
    # We'll use the sample PDF from farmer_factory/sample_docs/
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # Verify we got at least one page
    assert len(page_paths) > 0

    # Verify all pages exist and are PNGs
    for path in page_paths:
        assert path.exists()
        assert path.suffix == ".png"
        # Verify naming pattern
        assert path.stem.startswith(sample_pdf.stem)
        assert "_page_" in path.stem


def test_load_pdf_pages_creates_files(tmp_path):
    """Test that load_pdf_pages saves images to disk."""
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # Verify files were actually written
    for path in page_paths:
        # Check file size > 0 (not empty)
        assert path.stat().st_size > 0


def test_load_pdf_pages_naming_convention(tmp_path):
    """Test document ID naming convention."""
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # First page should be {stem}_page_0.png
    first_page = page_paths[0]
    expected_stem = f"{sample_pdf.stem}_page_0"
    assert first_page.stem == expected_stem
