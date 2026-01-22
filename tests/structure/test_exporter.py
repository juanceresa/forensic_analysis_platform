"""Unit tests for Graph Exporter."""

import pytest
from farmer_factory.structure.exporter import GraphExporter
from farmer_factory.structure import KnowledgeGraph


def test_normalize_date_iso_format():
    """Test date normalization for ISO 8601 dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Full ISO date should pass through
    assert exporter._normalize_date("1958-03-15") == "1958-03-15"
    assert exporter._normalize_date("1920-01-01") == "1920-01-01"


def test_normalize_date_year_only():
    """Test date normalization for year-only dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Year only should become January 1
    assert exporter._normalize_date("1920") == "1920-01-01"
    assert exporter._normalize_date("1958") == "1958-01-01"


def test_normalize_date_month_year():
    """Test date normalization for month/year formats."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Month/year should become first of month
    assert exporter._normalize_date("March 1958") == "1958-03-01"
    assert exporter._normalize_date("January 1920") == "1920-01-01"
    assert exporter._normalize_date("December 1961") == "1961-12-01"


def test_normalize_date_invalid():
    """Test date normalization with invalid dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Invalid dates should return original string
    assert exporter._normalize_date("unknown") == "unknown"
    assert exporter._normalize_date("") == ""
    assert exporter._normalize_date("not a date") == "not a date"
