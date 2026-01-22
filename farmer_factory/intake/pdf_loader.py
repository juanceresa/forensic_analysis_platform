"""PDF loading and document grouping."""

import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict


class PDFLoadError(Exception):
    """Exception raised when PDF loading fails."""
    pass


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

    def group_documents(self, pdf_files: List[Path]) -> Dict[str, List[Path]]:
        """
        Group PDFs by base filename.

        Args:
            pdf_files: List of PDF file paths

        Returns:
            Dict mapping logical document name to list of PDF parts (sorted)
        """
        groups: Dict[str, List[tuple[int, Path]]] = {}

        for pdf_file in pdf_files:
            base_name = self._extract_base_name(pdf_file.name)
            part_number = self._extract_part_number(pdf_file.name)

            if base_name not in groups:
                groups[base_name] = []

            groups[base_name].append((part_number, pdf_file))

        # Sort by part number and return just the paths
        return {
            base_name: [path for _, path in sorted(parts)]
            for base_name, parts in groups.items()
        }


class PDFLoader:
    """Extract page images from PDF documents."""

    def __init__(self, dpi: int = 300):
        """Initialize with target DPI for extraction."""
        self.dpi = dpi

    def load_document_group(
        self,
        pdf_parts: List[Path],
        output_dir: Path
    ) -> List[Path]:
        """
        Extract pages from multiple PDF parts into sequential images.

        Args:
            pdf_parts: List of PDF files (sorted) that form one document
            output_dir: Directory for output images

        Returns:
            List of all page image paths in order

        Raises:
            PDFLoadError: If any PDF cannot be read or is corrupted
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        page_paths = []
        page_number = 1

        for pdf_path in pdf_parts:
            try:
                doc = fitz.open(pdf_path)

                for page in doc:
                    output_path = output_dir / f"page_{page_number:03d}.png"
                    self._extract_page(page, output_path)
                    page_paths.append(output_path)
                    page_number += 1

                doc.close()

            except Exception as e:
                raise PDFLoadError(f"Failed to load PDF {pdf_path}: {e}")

        return page_paths

    def _extract_page(self, page: fitz.Page, output_path: Path) -> None:
        """Extract single page to PNG at target DPI."""
        # Calculate zoom factor for target DPI
        zoom = self.dpi / 72  # PDF default is 72 DPI
        mat = fitz.Matrix(zoom, zoom)

        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat)

        # Save as PNG
        pix.save(output_path)
