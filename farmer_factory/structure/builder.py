"""Graph builder for constructing knowledge graph from extraction results."""

from typing import List, Dict, Any
import logging
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver

logger = logging.getLogger(__name__)


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

    def add_extraction(self, extraction: ExtractionResult) -> None:
        """
        Add entities and relations from extraction result.

        Process:
        1. Resolve and add entities (with deduplication)
        2. Add relations (after entities exist)
        3. Update processing stats

        Args:
            extraction: ExtractionResult from extract module
        """
        # Track document processing
        self.processing_stats["documents_processed"] += 1

        # Process entities
        for entity in extraction.entities:
            self.processing_stats["entities_extracted"] += 1

            # Check if similar entity exists
            similar_id = self.resolver.find_similar_entity(entity, self.graph)

            if similar_id:
                # Merge with existing entity
                existing_data = self.graph.get_entity(similar_id)
                merged_data = self.resolver.merge_entities(existing_data, entity)

                # Update graph node
                self.graph.graph.nodes[similar_id].update(merged_data)

                self.processing_stats["entities_merged"] += 1
                logger.info(f"Merged entity {entity.id} into {similar_id}")
            else:
                # Add as new entity
                self.graph.add_entity(entity)
                logger.info(f"Added new entity {entity.id}")

        # Process relations
        for relation in extraction.relations:
            try:
                self.graph.add_relation(relation)
                self.processing_stats["relations_added"] += 1
                logger.info(f"Added relation {relation.id}: {relation.type}")
            except ValueError as e:
                logger.warning(f"Failed to add relation {relation.id}: {e}")
                # Skip invalid relations, continue processing

    def build_from_document_batch(
        self,
        extractions: List[ExtractionResult]
    ) -> None:
        """
        Process multiple document extractions.

        Args:
            extractions: List of ExtractionResult objects
        """
        logger.info(f"Processing batch of {len(extractions)} documents")

        for extraction in extractions:
            self.add_extraction(extraction)

        logger.info(
            f"Batch complete: {self.processing_stats['entities_extracted']} entities extracted, "
            f"{self.processing_stats['entities_merged']} merged, "
            f"{self.processing_stats['relations_added']} relations added"
        )
