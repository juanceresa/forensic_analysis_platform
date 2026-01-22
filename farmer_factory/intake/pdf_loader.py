"""PDF loading and document grouping."""

import re
from pathlib import Path
from typing import List, Dict


class DocumentGrouper:
    """Group multi-part PDF files into logical documents."""

    # Regex patterns for multi-part suffixes
    MULTIPART_PATTERNS = [
        r"\.(\d+)pdf\.pdf$",        # .1pdf.pdf, .2pdf.pdf
        r"_part(\d+)\.pdf$",        # _part1.pdf, _part2.pdf
        r"\s*\((\d+)\)\.pdf$",      # (1).pdf, (2).pdf
        r"-(\d+)\.pdf$",            # -1.pdf, -2.pdf
    ]

    def _extract_base_name(self, filename: str) -> str:
        """Remove multi-part suffixes to get base name."""
        # Try each pattern to remove suffixes (patterns include .pdf)
        for pattern in self.MULTIPART_PATTERNS:
            filename = re.sub(pattern, '.pdf', filename, flags=re.IGNORECASE)

        # Remove .pdf extension at the end
        if filename.lower().endswith('.pdf'):
            filename = filename[:-4]

        return filename

    def _extract_part_number(self, filename: str) -> int:
        """Extract part number from filename (0 if no part number)."""
        for pattern in self.MULTIPART_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0
