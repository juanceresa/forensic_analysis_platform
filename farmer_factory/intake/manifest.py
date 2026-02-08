"""Manifest management for intake batches."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

MAX_FOCUS_CONTEXT_LENGTH = 1500


class CaseFocus(BaseModel):
    """Per-case focus configuration from case.yaml."""

    primary_subjects: list[str] = Field(default_factory=list)
    primary_assets: list[str] = Field(default_factory=list)
    focus_context: str = ""

    @field_validator("primary_subjects", "primary_assets", mode="before")
    @classmethod
    def clean_list(cls, v: list) -> list[str]:
        """Strip whitespace and drop empty strings."""
        if not isinstance(v, list):
            return v
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]

    @field_validator("focus_context")
    @classmethod
    def truncate_context(cls, v: str) -> str:
        v = v.strip()
        if len(v) > MAX_FOCUS_CONTEXT_LENGTH:
            logger.warning(
                "focus_context truncated from %d to %d chars",
                len(v),
                MAX_FOCUS_CONTEXT_LENGTH,
            )
            return v[: MAX_FOCUS_CONTEXT_LENGTH - 3] + "..."
        return v

    @property
    def has_content(self) -> bool:
        """True if any focus field has actual content."""
        return bool(self.primary_subjects or self.primary_assets or self.focus_context)

    def to_prompt_section(self) -> str:
        """Format as text block for LLM prompt injection. Returns '' if no content."""
        if not self.has_content:
            return ""
        lines = ["## Case Focus"]
        if self.primary_subjects:
            lines.append(
                f"Primary subjects of interest: {', '.join(self.primary_subjects)}"
            )
        if self.primary_assets:
            lines.append(
                f"Primary assets of interest: {', '.join(self.primary_assets)}"
            )
        if self.focus_context:
            lines.append(f"Context: {self.focus_context}")
        lines.append(
            "Prioritize information about these subjects and assets, "
            "but do not exclude other relevant entities or events."
        )
        return "\n".join(lines)


def load_case_focus(case_dir: Path) -> CaseFocus | None:
    """Load case.yaml focus config. Returns None if missing or malformed."""
    case_yaml = case_dir / "case.yaml"
    if not case_yaml.exists():
        return None
    try:
        data = yaml.safe_load(case_yaml.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("%s is not a mapping, ignoring", case_yaml)
            return None
        focus_data = data.get("focus", {})
        if not isinstance(focus_data, dict):
            logger.warning("%s 'focus' is not a mapping, ignoring", case_yaml)
            return None
        focus = CaseFocus(**focus_data)
        return focus if focus.has_content else None
    except (yaml.YAMLError, ValidationError) as e:
        logger.warning("Failed to load %s: %s", case_yaml, e)
        return None


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
