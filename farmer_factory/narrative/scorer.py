"""Story centrality scoring algorithm for narrative focal point selection."""

from typing import Dict, List, Optional
import logging

from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


# Weight profiles for different use cases
WEIGHT_PROFILES = {
    "cuban_restitution": {
        "type_weights": {
            "PROPERTY": 10.0,
            "LOCATION": 8.0,
            "PERSON": 5.0,
            "ORGANIZATION": 3.0,
            "DOCUMENT": 1.0,
        },
        "relation_weights": {
            # Special events (highlighted)
            "CONFISCATED": 5.0,  # Expropriations critical
            "SOLD": 3.0,
            "INHERITED": 3.0,
            # Ownership
            "OWNS": 3.0,
            "BOUGHT": 2.5,
            # Other
            "LOCATED_IN": 1.5,
            "WITNESSED": 1.0,
            "NOTARIZED": 1.0,
            "EMPLOYED_BY": 1.0,
            "RELATED_TO": 0.5,
        },
        "connection_multiplier": 2.0,
        "document_multiplier": 3.0,
    }
}


class StoryScorer:
    """Calculate story centrality scores for entities in knowledge graph."""

    def __init__(
        self, profile: str = "cuban_restitution", custom_weights: Optional[Dict] = None
    ):
        """
        Initialize story scorer with weight profile.

        Args:
            profile: Weight profile name ("cuban_restitution")
            custom_weights: Optional custom weight overrides
        """
        if custom_weights:
            # Use custom weights
            self.type_weights = custom_weights.get("type_weights", {})
            self.relation_weights = custom_weights.get("relation_weights", {})
            self.connection_multiplier = custom_weights.get(
                "connection_multiplier", 2.0
            )
            self.document_multiplier = custom_weights.get("document_multiplier", 3.0)
        elif profile in WEIGHT_PROFILES:
            # Use named profile
            config = WEIGHT_PROFILES[profile]
            self.type_weights = config["type_weights"]
            self.relation_weights = config["relation_weights"]
            self.connection_multiplier = config["connection_multiplier"]
            self.document_multiplier = config["document_multiplier"]
        else:
            raise ValueError(f"Unknown profile: {profile}")

    def calculate_centrality(self, entity_id: str, graph: KnowledgeGraph) -> float:
        """
        Calculate story centrality score for an entity.

        Higher scores = better narrative focal points.

        Args:
            entity_id: Entity to score
            graph: Knowledge graph containing entity

        Returns:
            Centrality score (higher = more central to story)
        """
        entity_data = graph.get_entity(entity_id)
        if not entity_data:
            logger.warning(f"Entity {entity_id} not found in graph")
            return 0.0

        # Base score by entity type (use string key)
        entity_type = entity_data["entity_type"]
        base_score = self.type_weights.get(entity_type, 1.0)

        # Connection count (network importance)
        relations = graph.get_relations(entity_id, direction="both")
        connection_score = len(relations) * self.connection_multiplier

        # Document frequency (corroboration strength)
        extracted_from = entity_data.get("extracted_from", "")
        if extracted_from:
            doc_count = len([doc for doc in extracted_from.split(",") if doc.strip()])
        else:
            doc_count = 1
        document_score = doc_count * self.document_multiplier

        # Weighted relations (important relations matter more)
        weighted_relations = 0.0
        for relation in relations:
            rel_type_str = relation.get("relation_type", "")
            weighted_relations += self.relation_weights.get(rel_type_str, 1.0)

        total_score = (
            base_score + connection_score + document_score + weighted_relations
        )

        logger.debug(
            f"Entity {entity_id} centrality: {total_score:.2f} "
            f"(base={base_score}, conn={connection_score}, "
            f"doc={document_score}, rel={weighted_relations})"
        )

        return total_score

    def rank_entities(
        self, entity_ids: List[str], graph: KnowledgeGraph
    ) -> List[tuple[str, float]]:
        """
        Rank entities by story centrality.

        Args:
            entity_ids: Entities to rank
            graph: Knowledge graph

        Returns:
            List of (entity_id, score) tuples, sorted highest to lowest
        """
        scores = [
            (entity_id, self.calculate_centrality(entity_id, graph))
            for entity_id in entity_ids
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)
