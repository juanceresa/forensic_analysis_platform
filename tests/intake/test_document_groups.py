"""Tests for document grouping functionality."""

import pytest
from pathlib import Path
import tempfile
import shutil

from farmer_factory.intake.document_groups import (
    detect_groups,
    generate_draft_yaml,
    load_document_groups,
    validate_groups_against_files,
    DocumentGroup,
    DocumentGroupsConfig,
)


class TestDetectGroups:
    """Tests for automatic group detection."""

    def test_detects_numbered_suffix_pattern(self):
        """Should detect foo_1.pdf, foo_2.pdf pattern."""
        filenames = [
            "escritura_125_1.pdf",
            "escritura_125_2.pdf",
            "escritura_125_3.pdf",
            "other_doc.pdf",
        ]
        groups, standalone = detect_groups(filenames)

        assert "escritura_125" in groups
        assert len(groups["escritura_125"]) == 3
        assert groups["escritura_125"] == [
            "escritura_125_1.pdf",
            "escritura_125_2.pdf",
            "escritura_125_3.pdf",
        ]
        assert "other_doc.pdf" in standalone

    def test_detects_letter_suffix_pattern(self):
        """Should detect foo_a.pdf, foo_b.pdf pattern."""
        filenames = ["cert_a.pdf", "cert_b.pdf", "cert_c.pdf"]
        groups, standalone = detect_groups(filenames)

        assert "cert" in groups
        assert len(groups["cert"]) == 3

    def test_detects_parenthesis_pattern(self):
        """Should detect foo (1).pdf, foo (2).pdf pattern."""
        filenames = ["document (1).pdf", "document (2).pdf", "document (3).pdf"]
        groups, standalone = detect_groups(filenames)

        assert "document" in groups
        assert len(groups["document"]) == 3

    def test_detects_hyphen_pattern(self):
        """Should detect foo-1.pdf, foo-2.pdf pattern."""
        filenames = ["scan-1.pdf", "scan-2.pdf"]
        groups, standalone = detect_groups(filenames)

        assert "scan" in groups
        assert len(groups["scan"]) == 2

    def test_detects_page_indicator_pattern(self):
        """Should detect fooP1.pdf, fooP2.pdf pattern."""
        filenames = ["escrituraP1.pdf", "escrituraP2.pdf", "escrituraP3.pdf"]
        groups, standalone = detect_groups(filenames)

        assert "escritura" in groups
        assert len(groups["escritura"]) == 3

    def test_single_file_not_grouped(self):
        """Single file matching pattern should not form a group."""
        filenames = ["escritura_125_1.pdf", "other_doc.pdf"]
        groups, standalone = detect_groups(filenames)

        assert len(groups) == 0
        assert "escritura_125_1.pdf" in standalone
        assert "other_doc.pdf" in standalone

    def test_sorts_files_numerically(self):
        """Should sort files by sequence number."""
        filenames = [
            "doc_10.pdf",
            "doc_2.pdf",
            "doc_1.pdf",
        ]
        groups, standalone = detect_groups(filenames)

        assert groups["doc"] == ["doc_1.pdf", "doc_2.pdf", "doc_10.pdf"]

    def test_sorts_files_alphabetically(self):
        """Should sort letter-suffixed files alphabetically."""
        filenames = ["doc_c.pdf", "doc_a.pdf", "doc_b.pdf"]
        groups, standalone = detect_groups(filenames)

        assert groups["doc"] == ["doc_a.pdf", "doc_b.pdf", "doc_c.pdf"]

    def test_multiple_groups(self):
        """Should detect multiple separate groups."""
        filenames = [
            "escritura_1.pdf",
            "escritura_2.pdf",
            "testamento_1.pdf",
            "testamento_2.pdf",
            "standalone.pdf",
        ]
        groups, standalone = detect_groups(filenames)

        assert len(groups) == 2
        assert "escritura" in groups
        assert "testamento" in groups
        assert "standalone.pdf" in standalone

    def test_ignores_non_pdf(self):
        """Should ignore non-PDF files."""
        filenames = ["doc_1.pdf", "doc_2.pdf", "doc_3.txt", "doc_4.jpg"]
        groups, standalone = detect_groups(filenames)

        assert "doc" in groups
        assert len(groups["doc"]) == 2


class TestDocumentGroupsConfig:
    """Tests for DocumentGroupsConfig model."""

    def test_valid_config(self):
        """Should accept valid configuration."""
        config = DocumentGroupsConfig(
            status="DRAFT",
            groups=[
                DocumentGroup(
                    id="test_group",
                    name="Test Group",
                    files=["file1.pdf", "file2.pdf"],
                )
            ],
            standalone=["other.pdf"],
        )
        assert config.status == "DRAFT"
        assert len(config.groups) == 1

    def test_status_case_insensitive(self):
        """Status should be normalized to uppercase."""
        config = DocumentGroupsConfig(status="draft")
        assert config.status == "DRAFT"

    def test_invalid_status_rejected(self):
        """Invalid status should raise error."""
        with pytest.raises(ValueError):
            DocumentGroupsConfig(status="PENDING")

    def test_is_confirmed(self):
        """is_confirmed should return True for CONFIRMED status."""
        draft = DocumentGroupsConfig(status="DRAFT")
        confirmed = DocumentGroupsConfig(status="CONFIRMED")

        assert not draft.is_confirmed()
        assert confirmed.is_confirmed()

    def test_get_group_for_file(self):
        """Should find group containing a file."""
        config = DocumentGroupsConfig(
            groups=[
                DocumentGroup(
                    id="group1",
                    files=["a.pdf", "b.pdf"],
                ),
                DocumentGroup(
                    id="group2",
                    files=["c.pdf", "d.pdf"],
                ),
            ]
        )

        assert config.get_group_for_file("a.pdf").id == "group1"
        assert config.get_group_for_file("c.pdf").id == "group2"
        assert config.get_group_for_file("other.pdf") is None

    def test_group_requires_two_files(self):
        """Group must have at least 2 files."""
        with pytest.raises(ValueError):
            DocumentGroup(id="test", files=["single.pdf"])


class TestGenerateAndLoadYaml:
    """Tests for YAML generation and loading."""

    def test_generate_and_load_roundtrip(self):
        """Should generate YAML that can be loaded back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            case_dir = Path(tmpdir)
            groups = {"escritura_125": ["e_1.pdf", "e_2.pdf"]}
            standalone = ["other.pdf"]

            yaml_path = generate_draft_yaml(case_dir, groups, standalone)

            assert yaml_path.exists()

            loaded = load_document_groups(case_dir)

            assert loaded is not None
            assert loaded.status == "DRAFT"
            assert len(loaded.groups) == 1
            assert loaded.groups[0].id == "escritura_125"
            assert loaded.groups[0].files == ["e_1.pdf", "e_2.pdf"]
            assert loaded.standalone == ["other.pdf"]

    def test_load_nonexistent_returns_none(self):
        """Should return None for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_document_groups(Path(tmpdir))
            assert result is None


class TestValidateGroupsAgainstFiles:
    """Tests for validation of groups against actual files."""

    def test_valid_groups_pass(self):
        """Valid groups should produce no errors."""
        config = DocumentGroupsConfig(
            groups=[
                DocumentGroup(id="g1", files=["a.pdf", "b.pdf"]),
            ],
            standalone=["c.pdf"],
        )
        actual_files = ["a.pdf", "b.pdf", "c.pdf"]

        errors = validate_groups_against_files(config, actual_files)

        assert len(errors) == 0

    def test_missing_grouped_file_detected(self):
        """Should detect when grouped file doesn't exist."""
        config = DocumentGroupsConfig(
            groups=[
                DocumentGroup(id="g1", files=["a.pdf", "missing.pdf"]),
            ],
        )
        actual_files = ["a.pdf", "b.pdf"]

        errors = validate_groups_against_files(config, actual_files)

        assert len(errors) >= 1
        assert any("missing.pdf" in e for e in errors)

    def test_unaccounted_file_detected(self):
        """Should detect files not in groups or standalone."""
        config = DocumentGroupsConfig(
            groups=[
                DocumentGroup(id="g1", files=["a.pdf", "b.pdf"]),
            ],
            standalone=[],
        )
        actual_files = ["a.pdf", "b.pdf", "unaccounted.pdf"]

        errors = validate_groups_against_files(config, actual_files)

        assert len(errors) >= 1
        assert any("unaccounted.pdf" in str(e) for e in errors)
