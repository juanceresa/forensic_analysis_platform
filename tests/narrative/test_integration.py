"""Integration tests for narrative generation with real graph."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Property,
    Person,
    Location,
    Organization,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def villa_aurelia_graph():
    """Create realistic Villa Aurelia graph with confiscation."""
    kg = KnowledgeGraph(case_id="TEST-CERESA")

    # Villa Aurelia (hub)
    prop = Property(
        id="prop_villa_aurelia_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        property_type="Rural estate",
        area=59.28,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.69
        ),
        extracted_from="doc_001"
    )
    kg.add_entity(prop)

    # Location
    location = Location(
        id="loc_manibon_001",
        name="Maniabón",
        entity_type=EntityType.LOCATION,
        location_type="Hacienda",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(location)

    # Mario Ceresa (co-heir)
    mario = Person(
        id="person_mario_001",
        name="Mario Ceresa Rodriguez",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(mario)

    # INRA (confiscator)
    inra = Organization(
        id="org_inra_001",
        name="Instituto Nacional de Reforma Agraria",
        entity_type=EntityType.ORGANIZATION,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(inra)

    # Relations
    rel1 = Relation(
        id="rel_001",
        type=RelationType.LOCATED_IN,
        source_id="prop_villa_aurelia_001",
        target_id="loc_manibon_001",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="Villa Aurelia ubicada en Maniabón"
    )
    kg.add_relation(rel1)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.INHERITED,
        source_id="person_mario_001",
        target_id="prop_villa_aurelia_001",
        date="1960-05-13",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="en concepto de coheredero"
    )
    kg.add_relation(rel2)

    rel3 = Relation(
        id="rel_003",
        type=RelationType.CONFISCATED,
        source_id="org_inra_001",
        target_id="prop_villa_aurelia_001",
        date="1960",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="segregado para el INRA doce caballerías"
    )
    kg.add_relation(rel3)

    return kg


@pytest.mark.integration
@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_villa_aurelia_narrative_generation(mock_api_client, villa_aurelia_graph):
    """Test full narrative generation for Villa Aurelia."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Mock LLM response
    mock_client_instance.call_with_retry.return_value = (
        "Villa Aurelia, a 59.28 caballería estate in Maniabón [①], "
        "passed to Mario Ceresa Rodriguez as co-heir in 1960 [②]. "
        "That same year, the Instituto Nacional de Reforma Agraria "
        "confiscated 12.99 caballerías under the Agrarian Reform Law [③]."
    )

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="test_session_001"
    )

    # Should identify property as hub
    assert result.focal_entity_id == "prop_villa_aurelia_001"
    assert result.focal_entity_name == "Villa Aurelia"

    # Should use Haiku (simple constellation: 4 entities)
    assert result.model_used == "haiku"

    # Should have narrative
    assert len(result.main_narrative) > 0
    assert "Villa Aurelia" in result.main_narrative

    # Should extract highlighted events
    assert len(result.highlighted_events) > 0
    confiscation_events = [e for e in result.highlighted_events if e.event_type == "CONFISCATED"]
    assert len(confiscation_events) == 1

    # Should have cost tracking
    assert result.generation_cost > 0


def test_hub_identification_prefers_property(villa_aurelia_graph):
    """Test that property is identified as hub over people."""
    from farmer_factory.narrative.constellation import ConstellationAnalyzer

    analyzer = ConstellationAnalyzer()

    # Click on Mario
    constellation, hub_id = analyzer.analyze(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph
    )

    # Should identify Villa Aurelia as hub
    assert hub_id == "prop_villa_aurelia_001"


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_session_cost_tracking(mock_api_client, villa_aurelia_graph):
    """Test that session costs accumulate correctly."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance
    mock_client_instance.call_with_retry.return_value = "Test narrative [①]."

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    # Generate first narrative
    result1 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    cost1 = generator.session_costs["sess_123"]
    assert cost1 > 0

    # Generate second narrative (different entity, same session)
    result2 = generator.generate(
        clicked_node_id="org_inra_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    cost2 = generator.session_costs["sess_123"]
    assert cost2 > cost1  # Should accumulate


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_cache_prevents_duplicate_generation(mock_api_client, villa_aurelia_graph):
    """Test that cache prevents redundant LLM calls."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance
    mock_client_instance.call_with_retry.return_value = "Cached narrative [①]."

    generator = NarrativeGenerator(api_key="test_key", use_cache=True)

    # Generate first time (cache miss)
    result1 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    assert not result1.from_cache
    assert mock_client_instance.call_with_retry.call_count == 1

    # Generate second time (cache hit)
    result2 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    assert result2.from_cache
    assert mock_client_instance.call_with_retry.call_count == 1  # No additional call
