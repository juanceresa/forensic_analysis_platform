"""Tests for DocumentGrouper."""

import pytest
from pathlib import Path
from farmer_factory.intake.pdf_loader import DocumentGrouper


def test_extract_base_name_no_suffix():
    """Test extracting base name from simple filename."""
    grouper = DocumentGrouper()
    assert grouper._extract_base_name("document.pdf") == "document"


def test_extract_base_name_with_multipart_suffix():
    """Test extracting base name from multi-part filename."""
    grouper = DocumentGrouper()
    assert grouper._extract_base_name("document.1pdf.pdf") == "document"
    assert grouper._extract_base_name("document.2pdf.pdf") == "document"


def test_extract_base_name_with_part_suffix():
    """Test extracting base name with _part suffix."""
    grouper = DocumentGrouper()
    assert grouper._extract_base_name("document_part1.pdf") == "document"
    assert grouper._extract_base_name("document_part2.pdf") == "document"
