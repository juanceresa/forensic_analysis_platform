"""Integration test for full graph workflow."""

import pytest
import json
from pathlib import Path
from farmer_factory.structure import (
    KnowledgeGraph,
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification,
)
from farmer_factory.export import GraphExporter


def test_full_graph_workflow(tmp_path):
    """Test complete workflow from graph creation to JSON export."""
    # Step 1: Create knowledge graph
    kg = KnowledgeGraph(case_id="integration_test_001")
    assert kg.case_id == "integration_test_001"
    assert kg.graph.number_of_nodes() == 0
    assert kg.graph.number_of_edges() == 0

    # Step 2: Add entities
    person = Person(
        id="person_mario",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        alternate_names=["Mario F. Ceresa"],
        birth_date="1920-03-15",
        nationality="Cuban",
        residence="Havana",
        roles=["Owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.92
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_aguaras",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        property_type="Rural Farm",
        address="Pinar del Rio",
        area=250.0,
        area_unit="hectares",
        registry_number="REG-1234",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)
    kg.add_entity(prop)

    assert kg.graph.number_of_nodes() == 2

    # Step 3: Add relation
    relation = Relation(
        id="rel_ownership",
        type=RelationType.OWNS,
        source_id="person_mario",
        target_id="property_aguaras",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90
        ),
        date="1958-06-15",
        document_id="doc_001"
    )

    kg.add_relation(relation)
    assert kg.graph.number_of_edges() == 1

    # Step 4: Export to JSON
    exporter = GraphExporter(kg)
    output_file = tmp_path / "graph_data.json"
    exporter.export_to_json(output_file, factory_version="1.0.0")

    assert output_file.exists()

    # Step 5: Validate JSON structure
    with open(output_file) as f:
        data = json.load(f)

    assert "metadata" in data
    assert "nodes" in data
    assert "edges" in data
    assert "verification_summary" in data
    assert "entity_type_summary" in data

    # Validate metadata
    assert data["metadata"]["case_id"] == "integration_test_001"
    assert data["metadata"]["factory_version"] == "1.0.0"
    assert data["metadata"]["entity_count"] == 2
    assert data["metadata"]["relation_count"] == 1

    # Validate nodes
    assert len(data["nodes"]) == 2
    node_ids = [node["id"] for node in data["nodes"]]
    assert "person_mario" in node_ids
    assert "property_aguaras" in node_ids

    # Validate edges
    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["source"] == "person_mario"
    assert edge["target"] == "property_aguaras"
    assert edge["relation_type"] == "OWNS"

    # Validate summaries
    assert data["verification_summary"]["TIER_3_AI"] == 3  # 2 entities + 1 relation
    assert data["entity_type_summary"]["PERSON"] == 1
    assert data["entity_type_summary"]["PROPERTY"] == 1
