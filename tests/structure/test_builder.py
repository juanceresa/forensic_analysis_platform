"""Unit tests for Graph Builder."""

import pytest
from farmer_factory.structure.builder import GraphBuilder
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver


def test_builder_initialization():
    """Test GraphBuilder can be initialized."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()

    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    assert builder is not None
    assert builder.graph == graph
    assert builder.resolver == resolver
    assert builder.processing_stats == {
        "documents_processed": 0,
        "entities_extracted": 0,
        "entities_merged": 0,
        "relations_added": 0
    }
