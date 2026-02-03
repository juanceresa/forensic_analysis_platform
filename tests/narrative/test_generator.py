"""Tests for batch case narrative generator."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from farmer_factory.narrative.generator import (
    CaseNarrativeGenerator,
    _get_period_label,
    _estimate_cost,
    _prompt_hash,
    _parse_observations,
)
from farmer_factory.narrative.models import CaseNarrative, ForensicObservation


# ── Helper function tests ─────────────────────────────────────────


def test_get_period_label_known_ranges():
    assert _get_period_label(1959, 1961) == "Expropriation Period"
    assert _get_period_label(1945, 1958) == "Post-War Era"
    assert _get_period_label(1930, 1944) == "Pre-War Period"
    assert _get_period_label(1910, 1929) == "Early Property Records"


def test_get_period_label_unknown_range():
    assert _get_period_label(1970, 1979) == "1970-1979"


def test_estimate_cost_positive():
    cost = _estimate_cost("hello world prompt", "response text here", "haiku")
    assert cost > 0


def test_estimate_cost_sonnet_more_expensive():
    prompt = "a " * 100
    response = "b " * 50
    haiku_cost = _estimate_cost(prompt, response, "haiku")
    sonnet_cost = _estimate_cost(prompt, response, "sonnet")
    assert sonnet_cost > haiku_cost


def test_prompt_hash_deterministic():
    h1 = _prompt_hash("hello", "world")
    h2 = _prompt_hash("hello", "world")
    assert h1 == h2
    assert len(h1) == 12


def test_prompt_hash_differs():
    h1 = _prompt_hash("hello")
    h2 = _prompt_hash("goodbye")
    assert h1 != h2


# ── Period grouping tests ─────────────────────────────────────────


class TestPeriodGrouping:
    def _make_gen(self) -> CaseNarrativeGenerator:
        with patch("farmer_factory.narrative.generator.ClaudeAPIClient"):
            return CaseNarrativeGenerator(api_key="test")

    def test_group_by_decade(self):
        gen = self._make_gen()
        docs = [
            {"id": "d1", "date": "1952-01-01"},
            {"id": "d2", "date": "1955-06-15"},
            {"id": "d3", "date": "1960-03-01"},
        ]
        groups = gen._group_by_decade(docs)
        assert "1950-1959" in groups
        assert "1960-1969" in groups
        assert len(groups["1950-1959"]) == 2
        assert len(groups["1960-1969"]) == 1

    def test_group_by_decade_skips_undated(self):
        gen = self._make_gen()
        docs = [
            {"id": "d1", "date": "1952-01-01"},
            {"id": "d2", "date": None},
            {"id": "d3"},
        ]
        groups = gen._group_by_decade(docs)
        assert len(groups) == 1
        assert len(groups["1950-1959"]) == 1

    def test_merge_sparse_periods(self):
        gen = self._make_gen()
        periods = {
            "1930-1939": [{"id": "d1"}],
            "1940-1949": [{"id": "d2"}],
            "1950-1959": [{"id": "d3"}, {"id": "d4"}, {"id": "d5"}],
        }
        merged = gen._merge_sparse_periods(periods)
        # 1930s and 1940s both <3 docs → merged
        assert "1930-1949" in merged
        # 1950s has >=3 docs → kept
        assert "1950-1959" in merged
        assert len(merged) == 2

    def test_merge_sparse_single_period(self):
        gen = self._make_gen()
        periods = {"1950-1959": [{"id": "d1"}]}
        merged = gen._merge_sparse_periods(periods)
        assert merged == periods

    def test_parse_period_key(self):
        gen = self._make_gen()
        assert gen._parse_period_key("1950-1959") == (1950, 1959)


# ── Cost guard tests ──────────────────────────────────────────────


class TestCostGuards:
    def test_cost_limit_raises(self):
        with patch("farmer_factory.narrative.generator.ClaudeAPIClient"):
            gen = CaseNarrativeGenerator(api_key="test", max_cost=1.0)
        gen.total_cost = 1.0
        with pytest.raises(RuntimeError, match="cost limit exceeded"):
            gen._call_llm("any prompt")

    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_model_downgrade_on_failure(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        # First call (sonnet) fails, second call (haiku) succeeds
        mock_client.call_standard.side_effect = [
            Exception("rate limit"),
            "fallback response",
        ]
        gen = CaseNarrativeGenerator(api_key="test", primary_model="sonnet")
        text, cost = gen._call_llm("test prompt")
        assert text == "fallback response"
        assert cost > 0
        assert gen.total_cost > 0

    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_cost_accumulates(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        mock_client.call_standard.return_value = "response"
        gen = CaseNarrativeGenerator(api_key="test", max_cost=10.0)
        gen._call_llm("prompt one")
        cost_after_first = gen.total_cost
        gen._call_llm("prompt two")
        assert gen.total_cost > cost_after_first


# ── Evidence population tests ─────────────────────────────────────


class TestEvidence:
    def test_extract_highlighted_confiscated(self):
        with patch("farmer_factory.narrative.generator.ClaudeAPIClient"):
            gen = CaseNarrativeGenerator(api_key="test")
        relations = [
            {"relation_type": "CONFISCATED", "source_name": "INRA", "target_name": "Villa Aurelia", "date": "1960"},
            {"relation_type": "OWNS", "source_name": "Mario", "target_name": "Villa Aurelia"},
        ]
        highlights = gen._extract_highlighted_events([], relations)
        assert len(highlights) == 1
        assert highlights[0].event_type == "CONFISCATED"
        assert "INRA" in highlights[0].summary

    def test_extract_highlighted_multiple_types(self):
        with patch("farmer_factory.narrative.generator.ClaudeAPIClient"):
            gen = CaseNarrativeGenerator(api_key="test")
        relations = [
            {"relation_type": "SOLD", "source_name": "A", "target_name": "B"},
            {"relation_type": "INHERITED", "source_name": "C", "target_name": "D"},
            {"relation_type": "MENTIONS", "source_name": "E", "target_name": "F"},
        ]
        highlights = gen._extract_highlighted_events([], relations)
        assert len(highlights) == 2
        types = {h.event_type for h in highlights}
        assert types == {"SOLD", "INHERITED"}


# ── Enriched response parsing tests ──────────────────────────────


class TestEnrichedResponseParsing:
    def _make_gen(self) -> CaseNarrativeGenerator:
        with patch("farmer_factory.narrative.generator.ClaudeAPIClient"):
            return CaseNarrativeGenerator(api_key="test")

    def test_parse_full_response(self):
        gen = self._make_gen()
        raw = (
            "The Confiscation\n"
            "---\n"
            "Villa Aurelia was seized by INRA in 1960.\n"
            "---\n"
            "OBSERVATIONS:\n"
            "Tax record shows 24 cab but deed shows 60 | HIGH\n"
            "No inheritance filing found for 1955 transfer | MEDIUM"
        )
        title, narrative, obs = gen._parse_enriched_response(raw, "fallback")
        assert title == "The Confiscation"
        assert "Villa Aurelia" in narrative
        assert len(obs) == 2
        assert obs[0].severity == "HIGH"
        assert obs[1].severity == "MEDIUM"

    def test_parse_no_observations(self):
        gen = self._make_gen()
        raw = "A Legacy Divided\n---\nThe family estate was split in 1948."
        title, narrative, obs = gen._parse_enriched_response(raw, "fallback")
        assert title == "A Legacy Divided"
        assert "1948" in narrative
        assert len(obs) == 0

    def test_parse_no_delimiters(self):
        gen = self._make_gen()
        raw = "Just plain narrative text with no structure."
        title, narrative, obs = gen._parse_enriched_response(raw, "fallback")
        assert title == "fallback"
        assert narrative == raw
        assert len(obs) == 0

    def test_parse_observations_only_no_severity(self):
        obs_text = "Missing notarial record\nInconsistent dates"
        result = _parse_observations(obs_text)
        assert len(result) == 2
        assert all(o.severity == "MEDIUM" for o in result)

    def test_parse_observations_with_severity(self):
        obs_text = "Critical gap in records | HIGH\nMinor date issue | LOW"
        result = _parse_observations(obs_text)
        assert result[0].severity == "HIGH"
        assert result[1].severity == "LOW"


# ── Period generation tests ───────────────────────────────────────


class TestPeriodGeneration:
    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_generate_period_parses_title_and_observations(self, mock_client_cls):
        """Period generation parses enriched response into title, narrative, observations."""
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        mock_client.call_standard.return_value = (
            "The Confiscation\n---\nVilla Aurelia was seized.\n---\n"
            "OBSERVATIONS:\nMissing deed | HIGH"
        )

        gen = CaseNarrativeGenerator(api_key="test", max_cost=10.0)
        gen.domain_context = ""
        period = gen._generate_period(
            case_id="TEST",
            period_key="1950-1959",
            label="Test Period",
            documents=[{"id": "d1", "name": "Doc1", "date": "1952"}],
            entities=[],
            relations=[],
        )
        assert period.title == "The Confiscation"
        assert "Villa Aurelia" in period.narrative
        assert len(period.forensic_observations) == 1
        assert period.forensic_observations[0].severity == "HIGH"
