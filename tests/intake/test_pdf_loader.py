"""Tests for PDFLoader."""

import pytest
import fitz  # PyMuPDF
from pathlib import Path
from farmer_factory.intake.pdf_loader import PDFLoader, PDFLoadError


def test_pdf_loader_init():
    """Test PDFLoader initialization."""
    loader = PDFLoader(dpi=300)
    assert loader.dpi == 300


def test_pdf_loader_default_dpi():
    """Test PDFLoader default DPI."""
    loader = PDFLoader()
    assert loader.dpi == 300


def test_load_document_group_single_page(tmp_path):
    """Test loading single-page PDF."""
    # Create test PDF
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size
    page.insert_text((50, 50), "Test content")
    doc.save(pdf_path)
    doc.close()

    # Test extraction
    loader = PDFLoader(dpi=150)  # Lower DPI for faster tests
    output_dir = tmp_path / "output"

    page_paths = loader.load_document_group([pdf_path], output_dir)

    assert len(page_paths) == 1
    assert page_paths[0].exists()
    assert page_paths[0].name == "page_001.png"


def test_load_document_group_multipage(tmp_path):
    """Test loading multi-page PDF."""
    # Create test PDF with 3 pages
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Page {i+1}")
    doc.save(pdf_path)
    doc.close()

    # Test extraction
    loader = PDFLoader(dpi=150)
    output_dir = tmp_path / "output"

    page_paths = loader.load_document_group([pdf_path], output_dir)

    assert len(page_paths) == 3
    assert all(p.exists() for p in page_paths)
    assert page_paths[0].name == "page_001.png"
    assert page_paths[1].name == "page_002.png"
    assert page_paths[2].name == "page_003.png"


def test_load_document_group_multipart(tmp_path):
    """Test loading multi-part PDF (multiple files)."""
    # Create two test PDFs
    pdf1 = tmp_path / "doc.pdf"
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Part 1, Page {i+1}")
    doc.save(pdf1)
    doc.close()

    pdf2 = tmp_path / "doc.1pdf.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Part 2, Page {i+1}")
    doc.save(pdf2)
    doc.close()

    # Test extraction
    loader = PDFLoader(dpi=150)
    output_dir = tmp_path / "output"

    page_paths = loader.load_document_group([pdf1, pdf2], output_dir)

    # Should have 2 + 3 = 5 pages sequentially numbered
    assert len(page_paths) == 5
    assert all(p.exists() for p in page_paths)
    assert page_paths[0].name == "page_001.png"
    assert page_paths[1].name == "page_002.png"
    assert page_paths[2].name == "page_003.png"
    assert page_paths[3].name == "page_004.png"
    assert page_paths[4].name == "page_005.png"
