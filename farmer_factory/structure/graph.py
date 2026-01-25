"""
Knowledge graph operations using NetworkX.

Provides graph construction, entity/relation management, and conflict resolution.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path
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
        self.graph = nx.MultiDiGraph()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeGraph":
        """Load a knowledge graph from graph_data.json."""
        graph_path = Path(path)
        data = json.loads(graph_path.read_text())
        metadata = data.get("metadata", {})
        case_id = metadata.get("case_id") or "unknown"
        graph = cls(case_id=case_id)

        created_at = metadata.get("created_at")
        if isinstance(created_at, str):
            try:
                graph.created_at = datetime.fromisoformat(created_at)
            except ValueError:
                pass

        updated_at = metadata.get("updated_at")
        if isinstance(updated_at, str):
            try:
                graph.updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                pass

        for node in data.get("nodes", []):
            node_id = node.get("id")
            if node_id is None:
                continue
            attrs = {k: v for k, v in node.items() if k != "id"}
            graph.graph.add_node(node_id, **attrs)

        links = data.get("links") or data.get("edges") or []
        for link in links:
            source = link.get("source")
            target = link.get("target")
            if source is None or target is None:
                continue
            attrs = {k: v for k, v in link.items() if k not in ("source", "target")}
            relation_id = attrs.get("relation_id")
            if relation_id:
                graph.graph.add_edge(source, target, key=relation_id, **attrs)
            else:
                graph.graph.add_edge(source, target, **attrs)

        return graph

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
            key=relation.id,
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
            for source, target, key, edge_data in self.graph.out_edges(entity_id, keys=True, data=True):
                relation_id = edge_data.get("relation_id", key)
                relations.append({
                    "source": source,
                    "target": target,
                    "relation_id": relation_id,
                    **edge_data
                })

        if direction in ("in", "both"):
            for source, target, key, edge_data in self.graph.in_edges(entity_id, keys=True, data=True):
                relation_id = edge_data.get("relation_id", key)
                relations.append({
                    "source": source,
                    "target": target,
                    "relation_id": relation_id,
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
