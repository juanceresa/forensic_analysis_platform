"""Constellation analysis for extracting graph components and identifying hubs."""

from typing import List, Set, Optional, Literal
import logging
import networkx as nx

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative.scorer import StoryScorer

logger = logging.getLogger(__name__)


class ConstellationAnalyzer:
    """Extract graph constellations and identify narrative focal points."""

    def __init__(self, scorer: Optional[StoryScorer] = None):
        """
        Initialize constellation analyzer.

        Args:
            scorer: Story centrality scorer (creates default if not provided)
        """
        self.scorer = scorer or StoryScorer()

    def extract_constellation(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph
    ) -> Set[str]:
        """
        Extract connected component (constellation) containing clicked node.

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph

        Returns:
            Set of entity IDs in same connected component
        """
        if not graph.graph.has_node(clicked_node_id):
            logger.warning(f"Node {clicked_node_id} not found in graph")
            return set()

        # Convert directed graph to undirected for component analysis
        undirected = graph.graph.to_undirected()

        # Find connected component containing clicked node
        for component in nx.connected_components(undirected):
            if clicked_node_id in component:
                logger.info(
                    f"Extracted constellation of {len(component)} entities "
                    f"around {clicked_node_id}"
                )
                return component

        # Isolated node
        return {clicked_node_id}

    def identify_hub(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Identify optimal narrative focal point within constellation.

        Uses story centrality scoring to find entity with highest
        narrative importance.

        Args:
            constellation: Set of entity IDs in constellation
            graph: Knowledge graph

        Returns:
            Entity ID of hub, or None if constellation empty
        """
        if not constellation:
            return None

        # Rank all entities in constellation
        ranked = self.scorer.rank_entities(
            entity_ids=list(constellation),
            graph=graph
        )

        if not ranked:
            return None

        hub_id, hub_score = ranked[0]
        logger.info(
            f"Identified hub: {hub_id} (score={hub_score:.2f}) "
            f"from {len(constellation)} candidates"
        )

        return hub_id

    def calculate_complexity(
        self,
        entity_count: int,
        relation_count: int,
        document_count: int
    ) -> float:
        """
        Calculate constellation complexity score.

        Args:
            entity_count: Number of entities in constellation
            relation_count: Number of relations
            document_count: Number of unique source documents

        Returns:
            Complexity score (higher = more complex)
        """
        complexity = (
            entity_count * 2.0 +
            relation_count * 1.5 +
            document_count * 3.0
        )
        return complexity

    def select_model(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph,
        complexity_threshold: float = 50.0
    ) -> Literal["haiku", "sonnet"]:
        """
        Select LLM model based on constellation complexity.

        Simple contexts use Haiku (cheap), complex use Sonnet (deep).

        Args:
            constellation: Set of entity IDs
            graph: Knowledge graph
            complexity_threshold: Complexity above which to use Sonnet

        Returns:
            "haiku" or "sonnet"
        """
        # Count entities
        entity_count = len(constellation)

        # Count relations within constellation
        all_relations = []
        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")
            # Only count relations between entities in constellation
            for rel in relations:
                source = rel.get("source")
                target = rel.get("target")
                if source in constellation and target in constellation:
                    all_relations.append(rel)

        relation_count = len(all_relations)

        # Count unique documents
        unique_docs = set()
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    docs = extracted_from.split(",")
                    unique_docs.update(docs)

        document_count = len(unique_docs)

        # Calculate complexity
        complexity = self.calculate_complexity(
            entity_count=entity_count,
            relation_count=relation_count,
            document_count=document_count
        )

        model = "sonnet" if complexity > complexity_threshold else "haiku"

        logger.info(
            f"Model selection: {model} "
            f"(complexity={complexity:.1f}, entities={entity_count}, "
            f"relations={relation_count}, docs={document_count})"
        )

        return model

    def analyze(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph
    ) -> tuple[Set[str], Optional[str]]:
        """
        Full constellation analysis: extract + identify hub.

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph

        Returns:
            (constellation_ids, hub_id)
        """
        constellation = self.extract_constellation(clicked_node_id, graph)
        hub_id = self.identify_hub(constellation, graph)
        return constellation, hub_id
