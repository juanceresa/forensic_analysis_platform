"""Graph builder for constructing knowledge graph from extraction results."""

from typing import List, Dict, Any
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver


class GraphBuilder:
    """Orchestrates graph construction from extraction results."""

    def __init__(self, knowledge_graph: KnowledgeGraph, resolver: EntityResolver):
        """
        Initialize graph builder.

        Args:
            knowledge_graph: KnowledgeGraph instance to build into
            resolver: EntityResolver for deduplication
        """
        self.graph = knowledge_graph
        self.resolver = resolver
        self.processing_stats: Dict[str, int] = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "entities_merged": 0,
            "relations_added": 0
        }
