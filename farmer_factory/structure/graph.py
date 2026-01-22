"""
Knowledge graph operations using NetworkX.

Provides graph construction, entity/relation management, and conflict resolution.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import networkx as nx

from .schema import (
    BaseEntity,
    Relation,
    GraphMetadata,
)


class KnowledgeGraph:
    """NetworkX-based knowledge graph for entity-relation data."""

    def __init__(self, case_id: str):
        """Initialize knowledge graph.

        Args:
            case_id: Unique identifier for this case
        """
        self.case_id = case_id
        self.graph = nx.DiGraph()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_entity(self, entity: BaseEntity) -> None:
        """Add entity as node with all attributes.

        Args:
            entity: Entity to add to graph
        """
        self.graph.add_node(
            entity.id,
            entity_type=entity.entity_type.value,
            verification=entity.verification.model_dump(),
            **entity.model_dump(exclude={'id', 'entity_type', 'verification'})
        )
        self.updated_at = datetime.now()

    def add_relation(self, relation: Relation) -> None:
        """Add relation as directed edge.

        Args:
            relation: Relation to add to graph

        Raises:
            ValueError: If source or target entity doesn't exist
        """
        if not self.graph.has_node(relation.source_id):
            raise ValueError(f"Source entity {relation.source_id} not found")
        if not self.graph.has_node(relation.target_id):
            raise ValueError(f"Target entity {relation.target_id} not found")

        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_id=relation.id,
            relation_type=relation.type.value,
            verification=relation.verification.model_dump(),
            **relation.model_dump(exclude={'id', 'type', 'source_id', 'target_id', 'verification'})
        )
        self.updated_at = datetime.now()

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve entity data by ID.

        Args:
            entity_id: Entity ID to retrieve

        Returns:
            Entity data dict or None if not found
        """
        if not self.graph.has_node(entity_id):
            return None
        return dict(self.graph.nodes[entity_id])

    def get_relations(self, entity_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """Get all relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "in", "out", or "both"

        Returns:
            List of relation dicts
        """
        relations = []

        if direction in ("out", "both"):
            for target in self.graph.successors(entity_id):
                edge_data = self.graph.edges[entity_id, target]
                relations.append({
                    "source": entity_id,
                    "target": target,
                    **edge_data
                })

        if direction in ("in", "both"):
            for source in self.graph.predecessors(entity_id):
                edge_data = self.graph.edges[source, entity_id]
                relations.append({
                    "source": source,
                    "target": entity_id,
                    **edge_data
                })

        return relations

    def get_metadata(self, factory_version: str) -> GraphMetadata:
        """Generate metadata for export.

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            GraphMetadata object
        """
        from collections import Counter

        # Count entity types
        entity_types = [data.get("entity_type") for _, data in self.graph.nodes(data=True)]
        entity_type_counts = Counter(entity_types)

        # Count documents
        document_count = entity_type_counts.get("DOCUMENT", 0)

        return GraphMetadata(
            case_id=self.case_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            factory_version=factory_version,
            entity_count=self.graph.number_of_nodes(),
            relation_count=self.graph.number_of_edges(),
            document_count=document_count,
            processing_stats={}
        )
