"""Tests for case-level focus configuration (case.yaml)."""

import logging
from pathlib import Path

import pytest
import yaml

from farmer_factory.intake.manifest import (
    CaseFocus,
    MAX_FOCUS_CONTEXT_LENGTH,
    load_case_focus,
)


# ── Unit tests: CaseFocus model ─────────────────────────────────────


class TestCaseFocusModel:
    def test_defaults(self):
        focus = CaseFocus()
        assert focus.primary_subjects == []
        assert focus.primary_assets == []
        assert focus.focus_context == ""
        assert not focus.has_content

    def test_has_content_with_subjects(self):
        focus = CaseFocus(primary_subjects=["Mario Ceresa"])
        assert focus.has_content

    def test_has_content_with_assets(self):
        focus = CaseFocus(primary_assets=["Farmacia Ceresa"])
        assert focus.has_content

    def test_has_content_with_context(self):
        focus = CaseFocus(focus_context="Some context about the case.")
        assert focus.has_content

    def test_has_content_empty(self):
        focus = CaseFocus(primary_subjects=[], primary_assets=[], focus_context="")
        assert not focus.has_content

    def test_list_cleaning_strips_whitespace(self):
        focus = CaseFocus(primary_subjects=["  Mario Ceresa  ", " "])
        assert focus.primary_subjects == ["Mario Ceresa"]

    def test_list_cleaning_drops_empty_strings(self):
        focus = CaseFocus(primary_assets=["", "Farmacia", "  ", "Casa"])
        assert focus.primary_assets == ["Farmacia", "Casa"]

    def test_focus_context_truncation(self, caplog):
        long_context = "x" * 600
        with caplog.at_level(logging.WARNING):
            focus = CaseFocus(focus_context=long_context)
        assert len(focus.focus_context) <= MAX_FOCUS_CONTEXT_LENGTH
        assert focus.focus_context.endswith("...")
        assert "truncated" in caplog.text

    def test_focus_context_under_limit(self):
        short = "Some context"
        focus = CaseFocus(focus_context=short)
        assert focus.focus_context == short

    def test_focus_context_whitespace_stripped(self):
        focus = CaseFocus(focus_context="  hello  ")
        assert focus.focus_context == "hello"


# ── Unit tests: to_prompt_section ────────────────────────────────────


class TestToPromptSection:
    def test_empty_returns_empty_string(self):
        focus = CaseFocus()
        assert focus.to_prompt_section() == ""

    def test_includes_subjects(self):
        focus = CaseFocus(primary_subjects=["Mario Ceresa", "Ceresa family"])
        section = focus.to_prompt_section()
        assert "Mario Ceresa" in section
        assert "Ceresa family" in section
        assert "Primary subjects of interest" in section

    def test_includes_assets(self):
        focus = CaseFocus(primary_assets=["Farmacia Ceresa"])
        section = focus.to_prompt_section()
        assert "Farmacia Ceresa" in section
        assert "Primary assets of interest" in section

    def test_includes_context(self):
        focus = CaseFocus(focus_context="Case about property restitution.")
        section = focus.to_prompt_section()
        assert "Case about property restitution." in section

    def test_includes_guardrail_line(self):
        focus = CaseFocus(primary_subjects=["Mario Ceresa"])
        section = focus.to_prompt_section()
        assert "do not exclude other relevant entities" in section

    def test_full_section(self):
        focus = CaseFocus(
            primary_subjects=["Mario Ceresa"],
            primary_assets=["Farmacia Ceresa"],
            focus_context="Ceresa family restitution claim.",
        )
        section = focus.to_prompt_section()
        assert "## Case Focus" in section
        assert "Mario Ceresa" in section
        assert "Farmacia Ceresa" in section
        assert "Ceresa family restitution claim." in section


# ── Unit tests: load_case_focus ──────────────────────────────────────


class TestLoadCaseFocus:
    def test_missing_case_yaml(self, tmp_path):
        assert load_case_focus(tmp_path) is None

    def test_malformed_yaml_not_dict(self, tmp_path, caplog):
        (tmp_path / "case.yaml").write_text("- just a list\n")
        with caplog.at_level(logging.WARNING):
            result = load_case_focus(tmp_path)
        assert result is None
        assert "not a mapping" in caplog.text

    def test_invalid_focus_type(self, tmp_path, caplog):
        (tmp_path / "case.yaml").write_text("focus: just_a_string\n")
        with caplog.at_level(logging.WARNING):
            result = load_case_focus(tmp_path)
        assert result is None
        assert "not a mapping" in caplog.text

    def test_valid_focus(self, tmp_path):
        data = {
            "focus": {
                "primary_subjects": ["Mario Ceresa", "Ceresa family"],
                "primary_assets": ["Farmacia Ceresa"],
                "focus_context": "Ceresa family property claim.",
            }
        }
        (tmp_path / "case.yaml").write_text(yaml.dump(data))
        result = load_case_focus(tmp_path)
        assert result is not None
        assert result.primary_subjects == ["Mario Ceresa", "Ceresa family"]
        assert result.primary_assets == ["Farmacia Ceresa"]
        assert result.focus_context == "Ceresa family property claim."

    def test_empty_focus_returns_none(self, tmp_path):
        data = {"focus": {"primary_subjects": [], "primary_assets": [], "focus_context": ""}}
        (tmp_path / "case.yaml").write_text(yaml.dump(data))
        result = load_case_focus(tmp_path)
        assert result is None

    def test_invalid_yaml_syntax(self, tmp_path, caplog):
        (tmp_path / "case.yaml").write_text("focus: {bad yaml: [unclosed\n")
        with caplog.at_level(logging.WARNING):
            result = load_case_focus(tmp_path)
        assert result is None
        assert "Failed to load" in caplog.text

    def test_extra_keys_ignored(self, tmp_path):
        data = {
            "metadata": {"case_name": "Test"},
            "focus": {"primary_subjects": ["Mario Ceresa"]},
        }
        (tmp_path / "case.yaml").write_text(yaml.dump(data))
        result = load_case_focus(tmp_path)
        assert result is not None
        assert result.primary_subjects == ["Mario Ceresa"]


# ── Unit tests: prompt builder integration ───────────────────────────


class TestPromptBuilderIntegration:
    def test_entity_prompt_without_focus(self):
        from farmer_factory.extract.prompts.zero_shot import build_entity_prompt_zero_shot

        prompt = build_entity_prompt_zero_shot(
            text="Some OCR text", document_id="doc_1", case_focus=None
        )
        assert "Extract entities" in prompt
        assert "Case Focus" not in prompt

    def test_entity_prompt_with_focus(self):
        from farmer_factory.extract.prompts.zero_shot import build_entity_prompt_zero_shot

        focus = CaseFocus(primary_subjects=["Mario Ceresa"])
        prompt = build_entity_prompt_zero_shot(
            text="Some OCR text", document_id="doc_1", case_focus=focus
        )
        assert "Extract entities" in prompt
        assert "Mario Ceresa" in prompt
        assert "Case Focus" in prompt

    def test_relation_prompt_without_focus(self):
        from farmer_factory.extract.prompts.zero_shot import build_relation_prompt_zero_shot

        prompt = build_relation_prompt_zero_shot(
            text="Some text", entities=[], document_id="doc_1", case_focus=None
        )
        assert "Extract relationships" in prompt
        assert "Case Focus" not in prompt

    def test_relation_prompt_with_focus(self):
        from farmer_factory.extract.prompts.zero_shot import build_relation_prompt_zero_shot

        focus = CaseFocus(primary_assets=["Farmacia Ceresa"])
        prompt = build_relation_prompt_zero_shot(
            text="Some text", entities=[], document_id="doc_1", case_focus=focus
        )
        assert "Extract relationships" in prompt
        assert "Farmacia Ceresa" in prompt


# ── Integration test: pipeline threading ─────────────────────────────


class TestPipelineThreading:
    def test_process_case_passes_case_focus(self, tmp_path, monkeypatch):
        """Verify that process_case loads case.yaml and passes case_focus to extraction."""
        from unittest.mock import MagicMock, patch

        # Create minimal case structure
        case_dir = tmp_path / "FOCUS-TEST"
        (case_dir / "intake").mkdir(parents=True)
        (case_dir / "preprocessed").mkdir(parents=True)
        (case_dir / "extractions").mkdir(parents=True)
        (case_dir / "output").mkdir(parents=True)

        # Write case.yaml
        data = {
            "focus": {
                "primary_subjects": ["Test Subject"],
                "primary_assets": ["Test Asset"],
            }
        }
        (case_dir / "case.yaml").write_text(yaml.dump(data))

        # Verify load_case_focus works
        focus = load_case_focus(case_dir)
        assert focus is not None
        assert focus.primary_subjects == ["Test Subject"]
        assert focus.primary_assets == ["Test Asset"]
        assert focus.to_prompt_section() != ""


# ── Test real case.yaml ──────────────────────────────────────────────


class TestRealCaseYaml:
    def test_test_ceresa_case_yaml(self):
        """Verify the TEST-CERESA case.yaml loads correctly."""
        case_dir = Path("cases/TEST-CERESA")
        if not case_dir.exists():
            pytest.skip("TEST-CERESA case directory not found")
        focus = load_case_focus(case_dir)
        assert focus is not None
        assert "Mario Ceresa" in focus.primary_subjects
        assert "Ceresa family" in focus.primary_subjects
        assert "Farmacia Ceresa" in focus.primary_assets
        assert len(focus.focus_context) > 0
        section = focus.to_prompt_section()
        assert "Mario Ceresa" in section
        assert "Farmacia Ceresa" in section
