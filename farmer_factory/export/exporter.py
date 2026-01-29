"""
Graph export logic.

Generates graph_data.json and handles Supabase upload.
"""

import json
from pathlib import Path
from typing import Dict, Any

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.core.exporter import GraphExporter as StructureGraphExporter


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
        exporter = StructureGraphExporter(self.graph)
        return exporter.to_json(factory_version)

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
