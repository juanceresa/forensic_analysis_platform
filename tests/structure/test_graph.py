"""Tests for knowledge graph operations."""

import pytest
from datetime import datetime
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


def test_knowledge_graph_init():
    """Test KnowledgeGraph initialization."""
    kg = KnowledgeGraph(case_id="case_001")
    assert kg.case_id == "case_001"
    assert kg.graph.number_of_nodes() == 0
    assert kg.graph.number_of_edges() == 0


def test_add_entity():
    """Test adding entity to graph."""
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

    assert kg.graph.number_of_nodes() == 1
    assert kg.graph.has_node("person_123")
    assert kg.graph.nodes["person_123"]["name"] == "Mario Ceresa"
    assert kg.graph.nodes["person_123"]["entity_type"] == "PERSON"


def test_add_relation():
    """Test adding relation to graph."""
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

    assert kg.graph.number_of_edges() == 1
    assert kg.graph.has_edge("person_123", "property_456")
    assert kg.graph.edges["person_123", "property_456", "rel_789"]["relation_type"] == "OWNS"


def test_add_multiple_relations_same_nodes():
    """Test adding multiple relations between same nodes."""
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

    owns_relation = Relation(
        id="rel_own",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    sold_relation = Relation(
        id="rel_sold",
        type=RelationType.SOLD,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.82
        )
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(owns_relation)
    kg.add_relation(sold_relation)

    assert kg.graph.number_of_edges() == 2
    assert kg.graph.edges["person_123", "property_456", "rel_own"]["relation_type"] == "OWNS"
    assert kg.graph.edges["person_123", "property_456", "rel_sold"]["relation_type"] == "SOLD"


def test_get_entity():
    """Test retrieving entity from graph."""
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
    retrieved = kg.get_entity("person_123")

    assert retrieved is not None
    assert retrieved["name"] == "Mario Ceresa"
    assert retrieved["entity_type"] == "PERSON"


def test_get_nonexistent_entity():
    """Test retrieving nonexistent entity returns None."""
    kg = KnowledgeGraph(case_id="case_001")
    assert kg.get_entity("nonexistent") is None


def test_add_relation_missing_source():
    """Test ValueError when source entity doesn't exist."""
    kg = KnowledgeGraph(case_id="case_001")

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
    kg.add_entity(prop)

    relation = Relation(
        id="rel_789",
        type=RelationType.OWNS,
        source_id="nonexistent_person",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    with pytest.raises(ValueError, match="Source entity.*not found"):
        kg.add_relation(relation)


def test_add_relation_missing_target():
    """Test ValueError when target entity doesn't exist."""
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

    relation = Relation(
        id="rel_789",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="nonexistent_property",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    with pytest.raises(ValueError, match="Target entity.*not found"):
        kg.add_relation(relation)


def test_get_relations_outbound():
    """Test get_relations with direction='out'."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )
    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.88),
        extracted_from="doc_001"
    )
    relation = Relation(
        id="rel_1",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85)
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(relation)

    # Outbound from person
    out_rels = kg.get_relations("person_123", direction="out")
    assert len(out_rels) == 1
    assert out_rels[0]["target"] == "property_456"

    # Outbound from property (should be empty)
    out_rels = kg.get_relations("property_456", direction="out")
    assert len(out_rels) == 0


def test_get_relations_inbound():
    """Test get_relations with direction='in'."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )
    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.88),
        extracted_from="doc_001"
    )
    relation = Relation(
        id="rel_1",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85)
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(relation)

    # Inbound to property
    in_rels = kg.get_relations("property_456", direction="in")
    assert len(in_rels) == 1
    assert in_rels[0]["source"] == "person_123"

    # Inbound to person (should be empty)
    in_rels = kg.get_relations("person_123", direction="in")
    assert len(in_rels) == 0


def test_get_relations_both():
    """Test get_relations with direction='both' (default)."""
    kg = KnowledgeGraph(case_id="case_001")

    person1 = Person(
        id="person_1",
        entity_type=EntityType.PERSON,
        name="Person 1",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )
    person2 = Person(
        id="person_2",
        entity_type=EntityType.PERSON,
        name="Person 2",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )
    person3 = Person(
        id="person_3",
        entity_type=EntityType.PERSON,
        name="Person 3",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )

    kg.add_entity(person1)
    kg.add_entity(person2)
    kg.add_entity(person3)

    # person1 -> person2, person3 -> person2
    rel1 = Relation(
        id="rel_1",
        type=RelationType.OWNS,
        source_id="person_1",
        target_id="person_2",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85)
    )
    rel2 = Relation(
        id="rel_2",
        type=RelationType.OWNS,
        source_id="person_3",
        target_id="person_2",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85)
    )
    kg.add_relation(rel1)
    kg.add_relation(rel2)

    # person2 has both inbound relations
    all_rels = kg.get_relations("person_2", direction="both")
    assert len(all_rels) == 2


def test_get_metadata():
    """Test get_metadata generates correct metadata."""
    kg = KnowledgeGraph(case_id="test_case")

    person = Person(
        id="person_1",
        entity_type=EntityType.PERSON,
        name="Test Person",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
        extracted_from="doc_001"
    )
    kg.add_entity(person)

    metadata = kg.get_metadata(factory_version="2.0.0")

    assert metadata.case_id == "test_case"
    assert metadata.factory_version == "2.0.0"
    assert metadata.entity_count == 1
    assert metadata.relation_count == 0


def test_load_from_json(tmp_path):
    """Test loading KnowledgeGraph from graph_data.json."""
    import json

    graph_data = {
        "metadata": {
            "case_id": "loaded_case",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-02T12:00:00"
        },
        "nodes": [
            {
                "id": "person_1",
                "entity_type": "PERSON",
                "name": "Test Person"
            },
            {
                "id": "property_1",
                "entity_type": "PROPERTY",
                "name": "Test Property"
            }
        ],
        "links": [
            {
                "source": "person_1",
                "target": "property_1",
                "relation_id": "rel_1",
                "relation_type": "OWNS"
            }
        ]
    }

    graph_file = tmp_path / "graph_data.json"
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f)

    kg = KnowledgeGraph.load(graph_file)

    assert kg.case_id == "loaded_case"
    assert kg.graph.number_of_nodes() == 2
    assert kg.graph.number_of_edges() == 1
    assert kg.graph.has_node("person_1")
    assert kg.graph.has_node("property_1")
    assert kg.graph.has_edge("person_1", "property_1")


def test_load_handles_missing_metadata(tmp_path):
    """Test load() handles missing or incomplete metadata."""
    import json

    graph_data = {
        "nodes": [{"id": "node_1", "name": "Test"}],
        "links": []
    }

    graph_file = tmp_path / "graph_data.json"
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f)

    kg = KnowledgeGraph.load(graph_file)

    assert kg.case_id == "unknown"
    assert kg.graph.number_of_nodes() == 1


def test_load_handles_edges_key(tmp_path):
    """Test load() handles 'edges' key as alternative to 'links'."""
    import json

    graph_data = {
        "metadata": {"case_id": "test"},
        "nodes": [
            {"id": "a", "name": "A"},
            {"id": "b", "name": "B"}
        ],
        "edges": [
            {"source": "a", "target": "b", "relation_type": "RELATED"}
        ]
    }

    graph_file = tmp_path / "graph_data.json"
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f)

    kg = KnowledgeGraph.load(graph_file)

    assert kg.graph.number_of_edges() == 1

