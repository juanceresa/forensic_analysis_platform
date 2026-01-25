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
