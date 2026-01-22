"""Entity resolution for deduplication and conflict handling."""

from typing import Optional, Dict, Any, List, Tuple
from rapidfuzz import fuzz
from farmer_factory.structure.schema import BaseEntity, EntityType
from farmer_factory.structure.graph import KnowledgeGraph


class EntityResolver:
    """Handles entity deduplication using fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize entity resolver.

        Args:
            similarity_threshold: Minimum similarity score for merge (0.0-1.0)

        Raises:
            ValueError: If threshold not in range [0.0, 1.0]
        """
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(f"Similarity threshold must be between 0.0 and 1.0, got {similarity_threshold}")

        self.threshold = similarity_threshold
        self.entity_index: Dict[str, List[str]] = {}  # {entity_type: [entity_ids]}

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate fuzzy similarity between two names.

        Uses token_sort_ratio for order-insensitive matching.

        Args:
            name1: First name to compare
            name2: Second name to compare

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0

        # Use token_sort_ratio for order-insensitive matching
        # This handles "Juan Pérez García" vs "García, Juan Pérez"
        score = fuzz.token_sort_ratio(name1.lower(), name2.lower())

        # Convert 0-100 scale to 0.0-1.0
        return score / 100.0

    def find_similar_entity(
        self,
        entity: BaseEntity,
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Find existing entity that matches this one.

        Uses fuzzy string matching on name and attribute comparison.

        Args:
            entity: New entity to match
            graph: KnowledgeGraph to search

        Returns:
            Entity ID if match found (similarity > threshold), None otherwise
        """
        entity_type_str = entity.entity_type.value

        # Get all entities of the same type from graph
        candidates = []
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("entity_type") == entity_type_str:
                candidates.append((node_id, node_data))

        # No candidates to match against
        if not candidates:
            return None

        # For Person entities, match by name
        if entity.entity_type == EntityType.PERSON:
            return self._find_similar_person(entity, candidates)

        # For other entity types, implement type-specific matching
        # For now, return None (no match)
        return None

    def _find_similar_person(
        self,
        person: BaseEntity,
        candidates: List[Tuple[str, Dict[str, Any]]]
    ) -> Optional[str]:
        """
        Find similar Person entity among candidates.

        Args:
            person: Person entity to match
            candidates: List of (entity_id, entity_data) tuples

        Returns:
            Entity ID if match found, None otherwise
        """
        best_match_id = None
        best_similarity = 0.0

        person_name = person.name if hasattr(person, 'name') else ""

        for entity_id, entity_data in candidates:
            candidate_name = entity_data.get("name", "")

            # Calculate name similarity
            similarity = self._calculate_name_similarity(person_name, candidate_name)

            # Track best match
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = entity_id

        # Return match if above threshold
        if best_similarity >= self.threshold:
            return best_match_id

        return None
