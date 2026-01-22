"""Graph exporter for converting to force-graph JSON format."""

import re
from typing import Dict, Any
from pathlib import Path
from farmer_factory.structure.graph import KnowledgeGraph


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
