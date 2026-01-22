"""Unit tests for Graph Exporter."""

import pytest
from farmer_factory.structure.exporter import GraphExporter
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person, Property, EntityType, Verification, VerificationTier,
    Relation, RelationType
)


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


def test_to_json_empty_graph():
    """Test exporting empty graph."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    result = exporter.to_json(factory_version="1.0.0")

    assert result["nodes"] == []
    assert result["links"] == []
    assert result["metadata"]["case_id"] == "test_case"
    assert result["metadata"]["entity_count"] == 0
    assert result["metadata"]["relation_count"] == 0


def test_to_json_with_entities():
    """Test exporting graph with entities."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add person
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1920",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    # Verify nodes
    assert len(result["nodes"]) == 1
    person_node = result["nodes"][0]
    assert person_node["id"] == "p1"
    assert person_node["entity_type"] == "PERSON"
    assert person_node["name"] == "Juan Pérez"
    assert person_node["birth_date"] == "1920"
    assert person_node["birth_date_sortable"] == "1920-01-01"  # Normalized

    # Verify metadata
    assert result["metadata"]["entity_count"] == 1


def test_to_json_with_relations():
    """Test exporting graph with relations."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add entities
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    property_entity = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(property_entity)

    # Add relation
    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        date="1958-03-15",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        )
    )
    graph.add_relation(relation)

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    # Verify links
    assert len(result["links"]) == 1
    link = result["links"][0]
    assert link["source"] == "p1"
    assert link["target"] == "prop1"
    assert link["relation_type"] == "OWNS"
    assert link["date"] == "1958-03-15"
    assert link["date_sortable"] == "1958-03-15"

    # Verify metadata
    assert result["metadata"]["relation_count"] == 1


def test_to_json_with_conflicting_dates():
    """Test export handles conflicting dates properly."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add person with conflicting birth dates (from merge)
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1920",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    # Manually update with conflicting dates (simulating merge)
    graph.graph.nodes["p1"]["birth_date"] = ["1920 (doc_001)", "1922 (doc_002)"]
    graph.graph.nodes["p1"]["extracted_from"] = ["doc_001", "doc_002"]

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    person_node = result["nodes"][0]
    assert person_node["birth_date"] == ["1920 (doc_001)", "1922 (doc_002)"]
    assert person_node["birth_date_earliest"] == "1920"  # Earliest for sorting
    assert person_node["birth_date_sortable"] == "1920-01-01"
