"""Tests for graph post-processing."""

import pytest
from farmer_factory.structure.core.postprocessor import GraphPostProcessor
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Location,
    Relation,
    Verification,
    VerificationTier,
)


@pytest.fixture
def sample_graph():
    """Create a graph with redundant edges."""
    graph = KnowledgeGraph(case_id="test_case")

    # Create location hierarchy: Florida -> Camaguey -> Cuba
    florida = Location(
        id="loc_florida",
        name="Florida",
        location_type="municipality",
        parent_location_id="loc_camaguey",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc",
    )
    camaguey = Location(
        id="loc_camaguey",
        name="Camaguey",
        location_type="province",
        parent_location_id="loc_cuba",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc",
    )
    cuba = Location(
        id="loc_cuba",
        name="Cuba",
        location_type="country",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc",
    )

    graph.add_entity(florida)
    graph.add_entity(camaguey)
    graph.add_entity(cuba)

    # Add LOCATED_IN relations (some redundant)
    # Direct: Florida -> Camaguey
    graph.add_relation(
        Relation(
            id="rel_1",
            type="LOCATED_IN",
            source_id="loc_florida",
            target_id="loc_camaguey",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        )
    )
    # Direct: Camaguey -> Cuba
    graph.add_relation(
        Relation(
            id="rel_2",
            type="LOCATED_IN",
            source_id="loc_camaguey",
            target_id="loc_cuba",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        )
    )
    # REDUNDANT: Florida -> Cuba (can be inferred from transitivity)
    graph.add_relation(
        Relation(
            id="rel_3",
            type="LOCATED_IN",
            source_id="loc_florida",
            target_id="loc_cuba",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        )
    )

    return graph


class TestGraphPostProcessor:
    """Tests for GraphPostProcessor."""

    def test_removes_transitive_located_in(self, sample_graph):
        """Should remove LOCATED_IN edges that can be inferred from path."""
        processor = GraphPostProcessor()

        # Before: 3 LOCATED_IN relations
        relations_before = list(sample_graph.graph.edges(data=True))
        assert len(relations_before) == 3

        # Process
        stats = processor.remove_redundant_edges(sample_graph)

        # After: should remove Florida->Cuba (redundant via Camaguey)
        relations_after = list(sample_graph.graph.edges(data=True))
        assert len(relations_after) == 2
        assert stats["edges_removed"] == 1

    def test_keeps_non_transitive_relations(self, sample_graph):
        """Should not remove edges for non-transitive relation types."""
        # Add non-transitive relation
        sample_graph.add_relation(
            Relation(
                id="rel_owns",
                type="OWNS",
                source_id="loc_florida",  # Weird but for testing
                target_id="loc_cuba",
                verification=Verification(
                    tier=VerificationTier.TIER_3_AI, confidence=0.9
                ),
            )
        )

        processor = GraphPostProcessor()
        processor.remove_redundant_edges(sample_graph)

        # OWNS should still exist
        owns_edges = [
            e
            for e in sample_graph.graph.edges(data=True)
            if e[2].get("relation_type") == "OWNS"
        ]
        assert len(owns_edges) == 1

    def test_handles_empty_graph(self):
        """Should handle empty graph without error."""
        graph = KnowledgeGraph(case_id="empty_case")
        processor = GraphPostProcessor()

        stats = processor.remove_redundant_edges(graph)

        assert stats["edges_removed"] == 0

    def test_removes_self_loops(self):
        """Should remove self-loops."""
        graph = KnowledgeGraph(case_id="loop_case")

        loc = Location(
            id="loc_test",
            name="Test",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test_doc",
        )
        graph.add_entity(loc)

        # Add self-loop manually
        graph.graph.add_edge("loc_test", "loc_test", key="self_loop")

        processor = GraphPostProcessor()
        stats = processor.remove_redundant_edges(graph)

        assert stats["self_loops_removed"] == 1
        assert len(list(graph.graph.edges())) == 0

    def test_dry_run_mode(self, sample_graph):
        """Dry run should report but not modify graph."""
        processor = GraphPostProcessor()

        # Before
        edges_before = sample_graph.graph.number_of_edges()

        # Dry run
        stats = processor.remove_redundant_edges(sample_graph, dry_run=True)

        # After - should be unchanged
        edges_after = sample_graph.graph.number_of_edges()
        assert edges_before == edges_after
        assert stats["edges_removed"] >= 1  # Still reports what would be removed


class TestLocationHierarchyValidation:
    """Tests for location hierarchy validation."""

    @pytest.fixture
    def hierarchy_graph(self):
        """Create graph with location hierarchy."""
        graph = KnowledgeGraph(case_id="hierarchy_test")

        # Create proper hierarchy: Miramar -> La Habana -> Cuba
        miramar = Location(
            id="loc_miramar",
            name="Miramar",
            location_type="neighborhood",
            nature="ADMINISTRATIVE",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test_doc",
        )
        habana = Location(
            id="loc_habana",
            name="La Habana",
            location_type="city",
            nature="ADMINISTRATIVE",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test_doc",
        )
        cuba = Location(
            id="loc_cuba",
            name="Cuba",
            location_type="country",
            nature="ADMINISTRATIVE",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test_doc",
        )

        graph.add_entity(miramar)
        graph.add_entity(habana)
        graph.add_entity(cuba)

        # Valid: Miramar -> Habana
        graph.add_relation(
            Relation(
                id="rel_1",
                type="LOCATED_IN",
                source_id="loc_miramar",
                target_id="loc_habana",
                verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            )
        )
        # Valid: Habana -> Cuba
        graph.add_relation(
            Relation(
                id="rel_2",
                type="LOCATED_IN",
                source_id="loc_habana",
                target_id="loc_cuba",
                verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            )
        )

        return graph

    def test_valid_hierarchy_no_warnings(self, hierarchy_graph):
        """Valid hierarchy should produce no warnings."""
        processor = GraphPostProcessor()

        warnings = processor.validate_location_hierarchy(hierarchy_graph)

        assert len(warnings) == 0

    def test_invalid_hierarchy_country_in_city(self, hierarchy_graph):
        """Country LOCATED_IN city should be flagged."""
        # Add invalid: Cuba -> Miramar (country in neighborhood)
        hierarchy_graph.add_relation(
            Relation(
                id="rel_invalid",
                type="LOCATED_IN",
                source_id="loc_cuba",
                target_id="loc_miramar",
                verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            )
        )

        processor = GraphPostProcessor()
        warnings = processor.validate_location_hierarchy(hierarchy_graph)

        assert len(warnings) >= 1
        assert any("loc_cuba" in w["source_id"] for w in warnings)

    def test_self_referential_location_flagged(self, hierarchy_graph):
        """Location LOCATED_IN itself should be flagged."""
        # Add self-reference
        hierarchy_graph.graph.add_edge(
            "loc_habana", "loc_habana", key="rel_self", relation_type="LOCATED_IN"
        )

        processor = GraphPostProcessor()
        warnings = processor.validate_location_hierarchy(hierarchy_graph)

        assert len(warnings) >= 1
        assert any(w["issue"] == "self_reference" for w in warnings)

    def test_cycle_detection(self, hierarchy_graph):
        """Circular LOCATED_IN chain should be flagged."""
        # Add cycle: Cuba -> Miramar (creates Miramar -> Habana -> Cuba -> Miramar)
        hierarchy_graph.add_relation(
            Relation(
                id="rel_cycle",
                type="LOCATED_IN",
                source_id="loc_cuba",
                target_id="loc_miramar",
                verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            )
        )

        processor = GraphPostProcessor()
        warnings = processor.validate_location_hierarchy(hierarchy_graph)

        assert len(warnings) >= 1
        assert any(w["issue"] == "cycle" for w in warnings)
