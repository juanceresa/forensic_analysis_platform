"""Unit tests for processing helper functions."""

import pytest
from pathlib import Path
from farmer_factory.processing.helpers import load_pdf_pages, save_extraction_json
from farmer_factory.extract.pipeline import ExtractionResult
from farmer_factory.prepare import DocumentPath
from farmer_factory.structure.schema import (
    Person,
    EntityType,
    VerificationTier,
    Verification
)


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


def test_save_extraction_json_includes_flags(tmp_path):
    """Test extraction flags are persisted in JSON output."""
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Test Person",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    extraction = ExtractionResult(
        entities=[person],
        relations=[],
        ocr_result=None,
        confidence_scores={"overall": 0.85},
        path=DocumentPath.TYPED,
        processing_metadata={},
        extraction_flags=["RELATION_EXTRACTION_FAILED"]
    )

    output_path = tmp_path / "extraction.json"
    save_extraction_json(extraction, output_path)

    data = output_path.read_text()
    assert "RELATION_EXTRACTION_FAILED" in data


def test_save_ocr_text_empty(tmp_path):
    """Test save_ocr_text handles None and empty OCR results."""
    from farmer_factory.processing.helpers import save_ocr_text

    output_path = tmp_path / "ocr" / "test.txt"

    # Test with None
    save_ocr_text(None, output_path)
    assert not output_path.exists()


def test_save_ocr_text_creates_directory(tmp_path):
    """Test save_ocr_text creates parent directories."""
    from farmer_factory.processing.helpers import save_ocr_text
    from farmer_factory.extract.ocr import OCRResult

    # Create a mock OCR result
    ocr_result = OCRResult(
        text="Test OCR content",
        confidence=0.95,
        page_confidence=[0.95],
        blocks=[],
        metadata={}
    )

    output_path = tmp_path / "nested" / "dir" / "ocr.txt"
    save_ocr_text(ocr_result, output_path)

    assert output_path.exists()
    assert output_path.read_text() == "Test OCR content"


def test_setup_logging_creates_file(tmp_path):
    """Test setup_logging creates log file and configures handlers."""
    from farmer_factory.processing.helpers import setup_logging
    import logging

    log_file = tmp_path / "logs" / "test.log"
    setup_logging(log_file)

    # Verify log file was created (directory gets created)
    assert log_file.parent.exists()

    # Log something to verify it works
    test_logger = logging.getLogger("test_setup_logging")
    test_logger.info("Test log message")

    # Verify handlers were added
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) >= 2  # file + console

