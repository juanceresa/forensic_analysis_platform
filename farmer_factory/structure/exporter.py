"""Graph exporter for converting to force-graph JSON format."""

import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from collections import Counter
from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class GraphExporter:
    """Converts NetworkX graph to force-graph JSON format."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize graph exporter.

        Args:
            knowledge_graph: KnowledgeGraph to export
        """
        self.graph = knowledge_graph

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize flexible date format to sortable ISO 8601.

        Examples:
        - "1958-03-15" → "1958-03-15"
        - "1920" → "1920-01-01"
        - "March 1958" → "1958-03-01"

        Args:
            date_str: Flexible date string

        Returns:
            ISO 8601 date string for sorting, or original if can't parse
        """
        if not date_str:
            return date_str

        # Already ISO 8601 format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # Year only (4 digits)
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-01-01"

        # Month Year format (e.g., "March 1958")
        month_names = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12"
        }

        for month_name, month_num in month_names.items():
            if month_name in date_str.lower():
                # Extract year
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = year_match.group()
                    return f"{year}-{month_num}-01"

        # Can't parse, return original
        return date_str

    def to_json(self, factory_version: str) -> Dict[str, Any]:
        """
        Export graph to force-graph JSON format.

        Includes date normalization for sorting:
        - Converts flexible dates to ISO 8601 where possible
        - Adds computed fields (*_earliest, *_sortable)
        - Generates date_range metadata
        - Calculates verification distribution

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            Complete JSON structure with nodes, links, metadata
        """
        nodes = []
        links = []

        # Export nodes
        for node_id, node_data in self.graph.graph.nodes(data=True):
            node = {"id": node_id, **node_data}

            # Add sortable date fields
            self._add_sortable_date_fields(node)

            nodes.append(node)

        # Export links
        for source, target, edge_data in self.graph.graph.edges(data=True):
            link = {
                "source": source,
                "target": target,
                **edge_data
            }

            # Add sortable date field for relations
            if "date" in link:
                link["date_sortable"] = self._normalize_date(link["date"])

            links.append(link)

        # Generate metadata
        metadata = self._generate_metadata(factory_version, nodes, links)

        return {
            "nodes": nodes,
            "links": links,
            "metadata": metadata
        }

    def _add_sortable_date_fields(self, node: Dict[str, Any]) -> None:
        """
        Add sortable date fields to node.

        For conflicting dates (lists), adds *_earliest and *_sortable fields.

        Args:
            node: Node dictionary to modify in-place
        """
        date_fields = ["birth_date", "death_date", "date"]

        for field in date_fields:
            if field not in node:
                continue

            value = node[field]

            if isinstance(value, list):
                # Extract dates from provenance strings
                dates = []
                for item in value:
                    # Extract date part (before parenthesis)
                    date_part = item.split(" (")[0] if " (" in item else item
                    dates.append(date_part)

                # Find earliest
                earliest = min(dates) if dates else ""
                node[f"{field}_earliest"] = earliest
                node[f"{field}_sortable"] = self._normalize_date(earliest)
            elif isinstance(value, str):
                # Single value
                node[f"{field}_sortable"] = self._normalize_date(value)

    def _generate_metadata(
        self,
        factory_version: str,
        nodes: List[Dict],
        links: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate metadata for export.

        Args:
            factory_version: Version string
            nodes: List of node dicts
            links: List of link dicts

        Returns:
            Metadata dictionary
        """
        # Get base metadata from graph
        base_metadata = self.graph.get_metadata(factory_version)

        # Calculate verification distribution
        verification_dist = Counter()
        for node in nodes:
            tier = node.get("verification", {}).get("tier", "TIER_3_AI")
            verification_dist[tier] += 1

        # Calculate date range
        date_range = self._calculate_date_range(nodes, links)

        return {
            **base_metadata.model_dump(),
            "verification_distribution": dict(verification_dist),
            "date_range": date_range
        }

    def _calculate_date_range(
        self,
        nodes: List[Dict],
        links: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate earliest and latest dates in graph.

        Args:
            nodes: List of node dicts
            links: List of link dicts

        Returns:
            Dictionary with date range information
        """
        all_dates = []

        # Collect dates from nodes
        for node in nodes:
            for field in ["date", "birth_date", "death_date"]:
                if f"{field}_sortable" in node:
                    all_dates.append(node[f"{field}_sortable"])

        # Collect dates from links
        for link in links:
            if "date_sortable" in link:
                all_dates.append(link["date_sortable"])

        # Filter out non-date strings
        valid_dates = [d for d in all_dates if re.match(r'^\d{4}-\d{2}-\d{2}$', d)]

        if not valid_dates:
            return {
                "earliest_document": None,
                "latest_document": None,
                "earliest_event": None,
                "latest_event": None
            }

        return {
            "earliest_document": min(valid_dates),
            "latest_document": max(valid_dates),
            "earliest_event": min(valid_dates),
            "latest_event": max(valid_dates)
        }

    def save(self, output_path: Path, factory_version: str) -> None:
        """
        Save graph to JSON file with atomic write.

        Uses temp file + rename for atomic write to prevent corruption.

        Args:
            output_path: Path to save JSON file
            factory_version: Version string for Farmer Factory
        """
        # Export to JSON
        data = self.to_json(factory_version)

        # Atomic write: write to temp file, then rename
        temp_path = output_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

            # Atomic rename
            temp_path.rename(output_path)

            logger.info(f"Saved graph to {output_path} ({len(data['nodes'])} nodes, {len(data['links'])} links)")
        except Exception as e:
            # Clean up temp file if write failed
            if temp_path.exists():
                temp_path.unlink()
            raise
