"""Tests for story centrality scoring algorithm."""

import pytest
from farmer_factory.narrative.scorer import StoryScorer
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
def sample_graph():
    """Create sample graph with property, people, and confiscation."""
    kg = KnowledgeGraph(case_id="test_001")

    # Property
    property = Property(
        id="prop_001",
        entity_type=EntityType.PROPERTY,
        name="Villa Aurelia",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.92
        ),
        extracted_from="doc_001,doc_003,doc_007"
    )
    kg.add_entity(property)

    # Owner
    person1 = Person(
        id="person_001",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.89
        ),
        extracted_from="doc_001,doc_003"
    )
    kg.add_entity(person1)

    # INRA (confiscator)
    from farmer_factory.structure.schema import Organization
    inra = Organization(
        id="org_001",
        entity_type=EntityType.ORGANIZATION,
        name="INRA",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.74
        ),
        extracted_from="doc_012"
    )
    kg.add_entity(inra)

    # Ownership relation
    rel1 = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.90
        ),
        extracted_from="doc_001"
    )
    kg.add_relation(rel1)

    # Confiscation relation (should boost score)
    rel2 = Relation(
        id="rel_002",
        type=RelationType.CONFISCATED,
        source_id="org_001",
        target_id="prop_001",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.74
        ),
        extracted_from="doc_012"
    )
    kg.add_relation(rel2)

    return kg


def test_scorer_initialization():
    """Test StoryScorer initialization."""
    scorer = StoryScorer()
    assert scorer is not None


def test_property_scores_highest(sample_graph):
    """Test that properties score higher than people."""
    scorer = StoryScorer()

    prop_score = scorer.calculate_centrality("prop_001", sample_graph)
    person_score = scorer.calculate_centrality("person_001", sample_graph)

    assert prop_score > person_score


def test_confiscation_boosts_score(sample_graph):
    """Test that confiscation relations increase property score."""
    scorer = StoryScorer()

    # Property with confiscation should score very high
    score = scorer.calculate_centrality("prop_001", sample_graph)

    # Base property (10) + connections (2*2=4) + docs (3*3=9) +
    # OWNS (3.0) + CONFISCATED (5.0) = 31.0
    assert score >= 30.0


def test_weight_profile_system():
    """Test custom weight profiles."""
    custom_weights = {
        "type_weights": {
            EntityType.PROPERTY: 15.0,  # Boost properties
            EntityType.PERSON: 3.0
        },
        "relation_weights": {
            RelationType.CONFISCATED: 10.0  # Boost confiscations more
        }
    }

    scorer = StoryScorer(profile="custom", custom_weights=custom_weights)

    assert scorer.type_weights[EntityType.PROPERTY] == 15.0
    assert scorer.relation_weights[RelationType.CONFISCATED] == 10.0


def test_scorer_handles_missing_entity():
    """Test scorer handles missing entity gracefully."""
    kg = KnowledgeGraph(case_id="test_001")
    scorer = StoryScorer()

    score = scorer.calculate_centrality("nonexistent_001", kg)
    assert score == 0.0


def test_rank_entities(sample_graph):
    """Test ranking multiple entities."""
    scorer = StoryScorer()

    entity_ids = ["prop_001", "person_001", "org_001"]
    ranked = scorer.rank_entities(entity_ids, sample_graph)

    # Should return list of (id, score) tuples
    assert len(ranked) == 3
    assert ranked[0][0] == "prop_001"  # Property highest

    # Scores should be descending
    assert ranked[0][1] >= ranked[1][1]
    assert ranked[1][1] >= ranked[2][1]
