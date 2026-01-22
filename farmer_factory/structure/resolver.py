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

    def _calculate_name_similarity(self, name1: str, name2: Any) -> float:
        """
        Calculate fuzzy similarity between two names.

        Uses token_sort_ratio for order-insensitive matching.

        Args:
            name1: First name to compare
            name2: Second name to compare (can be list from conflict merges)

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0

        # Handle list (from conflict merges) - take first value
        if isinstance(name2, list):
            name2 = name2[0].split(" (")[0]  # Extract name before provenance

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

    def merge_entities(
        self,
        existing: Dict[str, Any],
        new: BaseEntity
    ) -> Dict[str, Any]:
        """
        Merge new entity data into existing entity.

        For conflicting fields, creates lists with document provenance:
        Example: birth_date = ["1920 (doc_001)", "1922 (doc_005)"]

        Args:
            existing: Existing entity data from graph
            new: New entity to merge in

        Returns:
            Merged entity data dictionary
        """
        merged = existing.copy()
        new_data = new.model_dump()

        # Handle extracted_from (always combine)
        existing_sources = existing.get("extracted_from", "")
        new_source = new_data.get("extracted_from", "")

        # Convert to list if needed
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources] if existing_sources else []
        if isinstance(new_source, str):
            new_source = [new_source] if new_source else []

        merged["extracted_from"] = list(set(existing_sources + new_source))

        # Merge other fields
        for field, new_value in new_data.items():
            if field in ("id", "entity_type", "extracted_from", "created_at", "updated_at"):
                continue  # Skip metadata fields

            existing_value = existing.get(field)

            # Handle None values
            if new_value is None:
                continue  # Keep existing value
            if existing_value is None:
                merged[field] = new_value
                continue

            # Handle list fields (union)
            if isinstance(new_value, list):
                if isinstance(existing_value, list):
                    merged[field] = list(set(existing_value + new_value))
                else:
                    merged[field] = new_value
                continue

            # Handle conflicts (different values)
            if existing_value != new_value:
                # Create provenance list
                existing_source = existing.get("extracted_from", ["unknown"])[0] if isinstance(existing.get("extracted_from"), list) else existing.get("extracted_from", "unknown")
                new_source_str = new_source[0] if new_source else "unknown"

                if isinstance(existing_value, list):
                    # Already a conflict list, append new value
                    merged[field] = existing_value + [f"{new_value} ({new_source_str})"]
                else:
                    # Create new conflict list
                    merged[field] = [
                        f"{existing_value} ({existing_source})",
                        f"{new_value} ({new_source_str})"
                    ]

        return merged
