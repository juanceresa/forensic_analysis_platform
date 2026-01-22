"""Entity resolution for deduplication and conflict handling."""

from typing import Optional, Dict, Any, List
from farmer_factory.structure.schema import BaseEntity
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
