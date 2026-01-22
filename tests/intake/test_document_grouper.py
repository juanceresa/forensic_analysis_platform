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


def test_extract_part_number_no_suffix():
    """Test extracting part number from simple filename."""
    grouper = DocumentGrouper()
    assert grouper._extract_part_number("document.pdf") == 0


def test_extract_part_number_with_multipart_suffix():
    """Test extracting part number from multi-part filename."""
    grouper = DocumentGrouper()
    assert grouper._extract_part_number("document.1pdf.pdf") == 1
    assert grouper._extract_part_number("document.2pdf.pdf") == 2


def test_extract_part_number_with_part_suffix():
    """Test extracting part number with _part suffix."""
    grouper = DocumentGrouper()
    assert grouper._extract_part_number("document_part1.pdf") == 1
    assert grouper._extract_part_number("document_part2.pdf") == 2


def test_group_documents_single_file():
    """Test grouping single PDF file."""
    grouper = DocumentGrouper()
    files = [Path("document.pdf")]

    groups = grouper.group_documents(files)

    assert len(groups) == 1
    assert "document" in groups
    assert groups["document"] == [Path("document.pdf")]


def test_group_documents_multipart():
    """Test grouping multi-part PDF files."""
    grouper = DocumentGrouper()
    files = [
        Path("will.pdf"),
        Path("will.1pdf.pdf"),
        Path("will.2pdf.pdf"),
    ]

    groups = grouper.group_documents(files)

    assert len(groups) == 1
    assert "will" in groups
    assert len(groups["will"]) == 3
    # Verify sorted order
    assert groups["will"][0].name == "will.pdf"
    assert groups["will"][1].name == "will.1pdf.pdf"
    assert groups["will"][2].name == "will.2pdf.pdf"


def test_group_documents_multiple_groups():
    """Test grouping multiple document groups."""
    grouper = DocumentGrouper()
    files = [
        Path("will.pdf"),
        Path("will.1pdf.pdf"),
        Path("deed.pdf"),
        Path("contract.pdf"),
    ]

    groups = grouper.group_documents(files)

    assert len(groups) == 3
    assert "will" in groups
    assert "deed" in groups
    assert "contract" in groups
    assert len(groups["will"]) == 2
    assert len(groups["deed"]) == 1
    assert len(groups["contract"]) == 1
