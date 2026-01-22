"""Manifest management for intake batches."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ManifestManager:
    """Manage case intake manifest."""

    def __init__(self, case_id: str):
        """Initialize manifest for a case."""
        self.case_id = case_id
        self.documents: List[Dict[str, Any]] = []
        self.intake_timestamp = datetime.now()

    def add_document(
        self,
        document_id: str,
        filename: str,
        status: str,
        part_count: int,
        page_count: int,
        error: Optional[str] = None
    ):
        """Add document to manifest."""
        doc_entry = {
            "document_id": document_id,
            "filename": filename,
            "status": status,
            "part_count": part_count,
            "page_count": page_count
        }

        if error:
            doc_entry["error"] = error

        self.documents.append(doc_entry)
