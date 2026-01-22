"""
Graph export logic.

Generates graph_data.json and handles Supabase upload.
"""

import json
from pathlib import Path
from typing import Dict, Any
from collections import Counter

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import GraphExport


class GraphExporter:
    """Export knowledge graph to JSON format."""

    def __init__(self, graph: KnowledgeGraph):
        """Initialize exporter.

        Args:
            graph: KnowledgeGraph to export
        """
        self.graph = graph

    def export_to_dict(self, factory_version: str) -> Dict[str, Any]:
        """Export graph to dictionary format.

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            Dictionary matching GraphExport schema
        """
        # Generate metadata
        metadata = self.graph.get_metadata(factory_version)

        # Collect nodes
        nodes = []
        for node_id, node_data in self.graph.graph.nodes(data=True):
            node_dict = {"id": node_id, **node_data}
            nodes.append(node_dict)

        # Collect edges
        edges = []
        for source, target, edge_data in self.graph.graph.edges(data=True):
            edge_dict = {
                "source": source,
                "target": target,
                **edge_data
            }
            edges.append(edge_dict)

        # Calculate verification summary
        verification_summary = self._calculate_verification_summary()

        # Calculate entity type summary
        entity_type_summary = self._calculate_entity_type_summary()

        # Build export dict
        export_data = {
            "metadata": metadata.model_dump(mode='json'),
            "nodes": nodes,
            "edges": edges,
            "verification_summary": verification_summary,
            "entity_type_summary": entity_type_summary,
            "date_range": None  # TODO: Calculate from document dates
        }

        return export_data

    def export_to_json(self, output_path: Path, factory_version: str) -> None:
        """Export graph to JSON file.

        Args:
            output_path: Path to write JSON file
            factory_version: Version string for Farmer Factory
        """
        data = self.export_to_dict(factory_version)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _calculate_verification_summary(self) -> Dict[str, int]:
        """Calculate verification tier counts.

        Returns:
            Dict mapping tier name to count
        """
        tiers = []

        # Count entity verification tiers
        for _, node_data in self.graph.graph.nodes(data=True):
            verification = node_data.get("verification", {})
            tier = verification.get("tier")
            if tier:
                tiers.append(tier)

        # Count relation verification tiers
        for _, _, edge_data in self.graph.graph.edges(data=True):
            verification = edge_data.get("verification", {})
            tier = verification.get("tier")
            if tier:
                tiers.append(tier)

        counts = Counter(tiers)

        # Ensure all tiers are present
        return {
            "TIER_3_AI": counts.get("TIER_3_AI", 0),
            "TIER_2_ANALYST": counts.get("TIER_2_ANALYST", 0),
            "TIER_2_INSTITUTIONAL": counts.get("TIER_2_INSTITUTIONAL", 0),
            "TIER_1_CERTIFIED": counts.get("TIER_1_CERTIFIED", 0),
        }

    def _calculate_entity_type_summary(self) -> Dict[str, int]:
        """Calculate entity type counts.

        Returns:
            Dict mapping entity type to count
        """
        entity_types = []

        for _, node_data in self.graph.graph.nodes(data=True):
            entity_type = node_data.get("entity_type")
            if entity_type:
                entity_types.append(entity_type)

        counts = Counter(entity_types)

        # Ensure all types are present
        return {
            "PERSON": counts.get("PERSON", 0),
            "PROPERTY": counts.get("PROPERTY", 0),
            "ORGANIZATION": counts.get("ORGANIZATION", 0),
            "LOCATION": counts.get("LOCATION", 0),
            "DOCUMENT": counts.get("DOCUMENT", 0),
        }
