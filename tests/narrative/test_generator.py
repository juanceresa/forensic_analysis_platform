"""Tests for narrative generator orchestrator."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Property,
    Person,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def sample_graph():
    """Create sample graph for testing."""
    kg = KnowledgeGraph(case_id="test_001")

    prop = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.92),
        extracted_from="doc_001, doc_003"
    )
    kg.add_entity(prop)

    person = Person(
        id="person_001",
        name="Mario Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.89),
        extracted_from="doc_001"
    )
    kg.add_entity(person)

    rel = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.90),
        extracted_from="doc_001"
    )
    kg.add_relation(rel)

    return kg


def test_generator_initialization():
    """Test NarrativeGenerator initialization."""
    generator = NarrativeGenerator(api_key="test_key")
    assert generator is not None


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_generate_narrative(mock_api_client, sample_graph):
    """Test full narrative generation pipeline."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Mock LLM response
    mock_client_instance.call_with_retry.return_value = (
        "Villa Aurelia was owned by Mario Ceresa [①]. "
        "The property was located in Maniabón [②]."
    )

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    assert result is not None
    assert result.focal_entity_id == "prop_001"  # Property is hub
    assert len(result.main_narrative) > 0
    assert result.generation_cost > 0


def test_session_cost_limit_exceeded(sample_graph):
    """Test that generator blocks at session cost limit."""
    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    # Manually set session cost above limit
    generator.session_costs["sess_123"] = 1.50  # Above $1 limit

    with pytest.raises(SessionCostLimitExceeded):
        generator.generate(
            clicked_node_id="person_001",
            graph=sample_graph,
            session_id="sess_123",
            max_cost_per_session=1.0
        )


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_simple_entity_narrative(mock_api_client, sample_graph):
    """Test narrative for simple entity (< 3 entities)."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Mock LLM response for simple narrative
    mock_client_instance.call_with_retry.return_value = (
        "Mario Ceresa appears as owner of Villa Aurelia in documents from 1952."
    )

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    # Should handle gracefully (2 entities < 3 threshold)
    assert result.is_simple_entity or len(result.main_narrative) > 0


def test_build_graph_context_dedupes_relations(sample_graph):
    """Test graph context relation list does not duplicate edges."""
    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    constellation = {"person_001", "prop_001"}
    context = generator._build_graph_context(
        focal_entity_id="prop_001",
        focal_entity_name="Villa Aurelia",
        focal_entity_type="PROPERTY",
        constellation=constellation,
        graph=sample_graph
    )

    assert len(context["relations"]) == 1
    assert "document_id" in context["relations"][0]
