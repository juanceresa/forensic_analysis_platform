"""Tests for constellation analysis (connected component extraction)."""

import pytest
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def multi_component_graph():
    """Graph with two separate constellations."""
    kg = KnowledgeGraph(case_id="test_001")

    # Constellation 1: Villa Aurelia + owners
    prop1 = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_entity(prop1)

    person1 = Person(
        id="person_001",
        name="Mario Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_entity(person1)

    rel1 = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_relation(rel1)

    # Constellation 2: Separate property + owner
    prop2 = Property(
        id="prop_002",
        name="Finca Rosa",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_entity(prop2)

    person2 = Person(
        id="person_002",
        name="Rosa Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_entity(person2)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.OWNS,
        source_id="person_002",
        target_id="prop_002",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_relation(rel2)

    return kg


def test_analyzer_initialization():
    """Test ConstellationAnalyzer initialization."""
    analyzer = ConstellationAnalyzer()
    assert analyzer is not None


def test_extract_constellation(multi_component_graph):
    """Test extracting connected component around a node."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    # Should contain prop_001 and person_001, but NOT prop_002/person_002
    assert len(constellation) == 2
    assert "person_001" in constellation
    assert "prop_001" in constellation
    assert "person_002" not in constellation


def test_identify_hub(multi_component_graph):
    """Test identifying narrative hub in constellation."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    hub_id = analyzer.identify_hub(
        constellation=constellation,
        graph=multi_component_graph
    )

    # Property should be identified as hub
    assert hub_id == "prop_001"


def test_model_selection_simple(multi_component_graph):
    """Test simple constellations use Haiku."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    model = analyzer.select_model(constellation, multi_component_graph)

    # 2 entities, 1 relation, 1 doc = complexity ~11 → Haiku
    assert model == "haiku"
