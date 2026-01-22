"""Manifest management for intake batches."""

import json
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

    def get_summary(self) -> Dict[str, int]:
        """Return success/failure/skipped counts."""
        successful = sum(1 for doc in self.documents if doc["status"] == "success")
        failed = sum(1 for doc in self.documents if doc["status"] == "failed")
        skipped = sum(1 for doc in self.documents if doc["status"] == "skipped")

        return {
            "total_documents": len(self.documents),
            "successful": successful,
            "failed": failed,
            "skipped": skipped
        }

    def save_manifest(self, output_path: Path):
        """Write manifest JSON to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self.get_summary()

        manifest_data = {
            "case_id": self.case_id,
            "intake_timestamp": self.intake_timestamp.isoformat() + "Z",
            **summary,
            "documents": self.documents
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
