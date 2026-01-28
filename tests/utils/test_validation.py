"""Tests for farmer_factory.utils security validation functions."""

import pytest
from pathlib import Path

from farmer_factory.utils import validate_case_id, get_safe_case_path, CASE_ID_PATTERN


class TestValidateCaseId:
    """Tests for validate_case_id function."""

    def test_valid_simple_case_id(self):
        """Test valid simple case IDs."""
        assert validate_case_id("TEST") is True
        assert validate_case_id("case001") is True
        assert validate_case_id("Case123") is True

    def test_valid_case_id_with_hyphen(self):
        """Test valid case IDs with hyphens."""
        assert validate_case_id("TEST-CERESA") is True
        assert validate_case_id("case-001") is True
        assert validate_case_id("CASE-ABC-123") is True

    def test_valid_case_id_with_underscore(self):
        """Test valid case IDs with underscores."""
        assert validate_case_id("TEST_CERESA") is True
        assert validate_case_id("case_001_alpha") is True

    def test_invalid_empty_case_id(self):
        """Test empty case ID is rejected."""
        assert validate_case_id("") is False
        assert validate_case_id(None) is False

    def test_invalid_path_traversal_dotdot(self):
        """Test path traversal with .. is rejected."""
        assert validate_case_id("../etc/passwd") is False
        assert validate_case_id("case/../admin") is False
        assert validate_case_id("..") is False
        assert validate_case_id("../../root") is False

    def test_invalid_path_traversal_slash(self):
        """Test path traversal with / is rejected."""
        assert validate_case_id("case/admin") is False
        assert validate_case_id("/etc/passwd") is False
        assert validate_case_id("cases/private/data") is False

    def test_invalid_special_characters(self):
        """Test special characters are rejected."""
        assert validate_case_id("case;rm -rf /") is False
        assert validate_case_id("case$HOME") is False
        assert validate_case_id("case`whoami`") is False
        assert validate_case_id("case|cat /etc/passwd") is False
        assert validate_case_id("case&echo hacked") is False
        assert validate_case_id("case\ninjection") is False

    def test_invalid_whitespace(self):
        """Test whitespace is rejected."""
        assert validate_case_id("case name") is False
        assert validate_case_id(" case") is False
        assert validate_case_id("case ") is False
        assert validate_case_id("\tcase") is False


class TestGetSafeCasePath:
    """Tests for get_safe_case_path function."""

    def test_valid_case_id_returns_path(self):
        """Test valid case ID returns resolved path."""
        path = get_safe_case_path("TEST-CERESA")
        assert isinstance(path, Path)
        assert path.name == "TEST-CERESA"
        assert "cases" in str(path)

    def test_valid_case_id_with_custom_base(self, tmp_path):
        """Test valid case ID with custom base directory."""
        path = get_safe_case_path("mycase", base_dir=tmp_path)
        assert path == (tmp_path / "mycase").resolve()

    def test_invalid_case_id_raises_error(self):
        """Test invalid case ID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid case_id"):
            get_safe_case_path("../etc/passwd")

        with pytest.raises(ValueError, match="Invalid case_id"):
            get_safe_case_path("")

    def test_path_traversal_detection(self, tmp_path):
        """Test path traversal attempts are caught."""
        # This tests the secondary path.relative_to check
        with pytest.raises(ValueError):
            get_safe_case_path("../malicious", base_dir=tmp_path)


class TestCaseIdPattern:
    """Tests for CASE_ID_PATTERN regex."""

    def test_pattern_matches_valid(self):
        """Test regex matches valid patterns."""
        assert CASE_ID_PATTERN.match("TEST-CERESA")
        assert CASE_ID_PATTERN.match("case_001")
        assert CASE_ID_PATTERN.match("ABC123")

    def test_pattern_rejects_invalid(self):
        """Test regex rejects invalid patterns."""
        assert not CASE_ID_PATTERN.match("../etc")
        assert not CASE_ID_PATTERN.match("case/admin")
        assert not CASE_ID_PATTERN.match("case name")
        assert not CASE_ID_PATTERN.match("")
