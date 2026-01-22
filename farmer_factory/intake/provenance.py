"""Provenance tracking for document chain of custody."""

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ProvenanceTracker:
    """Track document provenance and chain of custody."""

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks for memory efficiency
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return f"sha256:{sha256_hash.hexdigest()}"

    def create_provenance(
        self,
        document_id: str,
        pdf_parts: List[Path],
        page_count: int,
        status: str,
        missing_parts: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Create provenance metadata for a document.

        Args:
            document_id: Unique document identifier
            pdf_parts: List of source PDF files
            page_count: Total pages extracted
            status: "success" or "failed"
            missing_parts: List of missing part numbers (optional)

        Returns:
            Provenance dict with hashes, timestamps, metadata
        """
        # Extract base filename from first part
        base_name = pdf_parts[0].stem
        if base_name.endswith('.1pdf'):
            base_name = base_name[:-5]  # Remove .1pdf

        source_files = []
        for pdf_path in pdf_parts:
            source_files.append({
                "filename": pdf_path.name,
                "file_hash": self._compute_file_hash(pdf_path),
                "file_size_bytes": pdf_path.stat().st_size,
                "pages_in_part": 0  # Will be set by caller if needed
            })

        return {
            "document_id": document_id,
            "original_filename": base_name,
            "part_count": len(pdf_parts),
            "source_files": source_files,
            "total_page_count": page_count,
            "intake_timestamp": datetime.now().isoformat() + "Z",
            "extraction_dpi": 300,
            "status": status,
            "missing_parts": missing_parts or []
        }
