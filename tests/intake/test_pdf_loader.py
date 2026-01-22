"""Tests for PDFLoader."""

import pytest
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
