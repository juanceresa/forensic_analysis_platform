"""Tests for graph export logic."""

import pytest
import json
from pathlib import Path
from farmer_factory.export.exporter import GraphExporter
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification,
)


def test_exporter_init():
    """Test GraphExporter initialization."""
    kg = KnowledgeGraph(case_id="case_001")
    exporter = GraphExporter(kg)
    assert exporter.graph == kg


def test_export_to_dict():
    """Test exporting graph to dict."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    relation = Relation(
        id="rel_789",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(relation)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert "metadata" in data
    assert "nodes" in data
    assert "links" in data

    assert data["metadata"]["case_id"] == "case_001"
    assert len(data["nodes"]) == 2
    assert len(data["links"]) == 1


def test_export_to_json(tmp_path):
    """Test exporting graph to JSON file."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)

    exporter = GraphExporter(kg)
    output_file = tmp_path / "graph_data.json"
    exporter.export_to_json(output_file, factory_version="1.0.0")

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data["metadata"]["case_id"] == "case_001"
    assert len(data["nodes"]) == 1


def test_verification_summary():
    """Test verification summary calculation."""
    kg = KnowledgeGraph(case_id="case_001")

    # Add entities with different verification tiers
    for i, tier in enumerate([VerificationTier.TIER_3_AI,
                               VerificationTier.TIER_3_AI,
                               VerificationTier.TIER_2_ANALYST]):
        person = Person(
            id=f"person_{i}",
            entity_type=EntityType.PERSON,
            name=f"Person {i}",
            verification=Verification(tier=tier, confidence=0.85),
            extracted_from="doc_001"
        )
        kg.add_entity(person)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert data["metadata"]["verification_distribution"]["TIER_3_AI"] == 2
    assert data["metadata"]["verification_distribution"]["TIER_2_ANALYST"] == 1


def test_entity_type_summary():
    """Test entity type summary calculation."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Person",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)
    kg.add_entity(prop)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert data["metadata"]["entity_type_summary"]["PERSON"] == 1
    assert data["metadata"]["entity_type_summary"]["PROPERTY"] == 1
