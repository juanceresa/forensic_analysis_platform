"""Document grouping for multi-file documents.

Detects and manages document groups where a single logical document
is split across multiple PDF files (e.g., escritura_125_1.pdf, escritura_125_2.pdf).

Workflow:
1. Auto-detect potential groupings from file naming patterns
2. Generate draft YAML for analyst review
3. Analyst confirms/edits groupings
4. Processing uses confirmed groupings to create unified DOCUMENT entities
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# Patterns for detecting multi-part documents
# Each pattern captures (base_name, sequence_indicator)
GROUPING_PATTERNS = [
    # foo.1pdf.pdf, foo.2pdf.pdf (common scan naming)
    re.compile(r"^(.+?)\.(\d+)pdf\.pdf$", re.IGNORECASE),
    # foo 1.pdf, foo 2.pdf (space before number)
    re.compile(r"^(.+?)\s+(\d+)\.pdf$", re.IGNORECASE),
    # foo_1.pdf, foo_2.pdf, foo_3.pdf
    re.compile(r"^(.+?)_(\d+)\.pdf$", re.IGNORECASE),
    # foo_a.pdf, foo_b.pdf, foo_c.pdf
    re.compile(r"^(.+?)_([a-z])\.pdf$", re.IGNORECASE),
    # foo (1).pdf, foo (2).pdf
    re.compile(r"^(.+?)\s*\((\d+)\)\.pdf$", re.IGNORECASE),
    # foo-1.pdf, foo-2.pdf
    re.compile(r"^(.+?)-(\d+)\.pdf$", re.IGNORECASE),
    # foo-a.pdf, foo-b.pdf
    re.compile(r"^(.+?)-([a-z])\.pdf$", re.IGNORECASE),
    # fooP1.pdf, fooP2.pdf (page indicator)
    re.compile(r"^(.+?)p(\d+)\.pdf$", re.IGNORECASE),
    # foo_page1.pdf, foo_page2.pdf
    re.compile(r"^(.+?)_?page(\d+)\.pdf$", re.IGNORECASE),
]


class DocumentGroup(BaseModel):
    """A group of files representing a single logical document."""

    id: str = Field(..., description="Unique identifier for the group")
    name: Optional[str] = Field(None, description="Human-readable name")
    document_type: Optional[str] = Field(None, description="Type of document")
    date: Optional[str] = Field(None, description="Document date if known")
    files: List[str] = Field(..., description="List of filenames in order")

    @field_validator("date", mode="before")
    @classmethod
    def coerce_date_to_str(cls, v: object) -> str | None:
        """YAML parses bare dates (e.g. 1946-04-01) into datetime.date objects."""
        if v is None:
            return v
        return str(v)

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("A document group must have at least 2 files")
        return v


class DocumentGroupsConfig(BaseModel):
    """Configuration for document groupings in a case."""

    status: str = Field(
        default="DRAFT",
        description="DRAFT (needs review) or CONFIRMED (ready to process)",
    )
    groups: List[DocumentGroup] = Field(default_factory=list)
    standalone: List[str] = Field(
        default_factory=list, description="Files not in any group"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.upper()
        if v not in ("DRAFT", "CONFIRMED"):
            raise ValueError("Status must be DRAFT or CONFIRMED")
        return v

    def is_confirmed(self) -> bool:
        """Check if groupings have been confirmed by analyst."""
        return self.status == "CONFIRMED"

    def get_group_for_file(self, filename: str) -> Optional[DocumentGroup]:
        """Get the group a file belongs to, if any."""
        for group in self.groups:
            if filename in group.files:
                return group
        return None

    def get_all_grouped_files(self) -> Set[str]:
        """Get all files that are part of a group."""
        files = set()
        for group in self.groups:
            files.update(group.files)
        return files


def detect_groups(filenames: List[str]) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Detect potential document groups from filename patterns.

    Args:
        filenames: List of PDF filenames

    Returns:
        Tuple of (groups dict {base_name: [files]}, standalone files list)
    """
    potential_groups: Dict[str, List[Tuple[str, str]]] = {}
    matched_files: Set[str] = set()

    for filename in filenames:
        if not filename.lower().endswith(".pdf"):
            continue

        for pattern in GROUPING_PATTERNS:
            match = pattern.match(filename)
            if match:
                base_name = match.group(1).strip()
                sequence = match.group(2)

                # Normalize base name (remove trailing underscores/hyphens)
                base_name = re.sub(r"[-_]+$", "", base_name)

                if base_name not in potential_groups:
                    potential_groups[base_name] = []
                potential_groups[base_name].append((filename, sequence))
                matched_files.add(filename)
                break  # Use first matching pattern

    # Filter to only groups with 2+ files and sort files within each group
    groups: Dict[str, List[str]] = {}
    for base_name, files_with_seq in potential_groups.items():
        if len(files_with_seq) >= 2:
            # Sort by sequence (numeric or alphabetic)
            sorted_files = sorted(files_with_seq, key=lambda x: _sort_key(x[1]))
            groups[base_name] = [f[0] for f in sorted_files]

    # Files not in any group (either didn't match patterns or were alone)
    standalone = [
        f
        for f in filenames
        if f not in matched_files or f not in _get_grouped_files(groups)
    ]

    # Also add files that matched a pattern but were alone (not a real group)
    for base_name, files_with_seq in potential_groups.items():
        if len(files_with_seq) < 2:
            for filename, _ in files_with_seq:
                if filename not in standalone:
                    standalone.append(filename)

    return groups, sorted(standalone)


def _sort_key(sequence: str) -> Tuple[int, str]:
    """Generate a sort key for sequence indicators."""
    try:
        return (0, str(int(sequence)).zfill(10))
    except ValueError:
        return (1, sequence.lower())


def _get_grouped_files(groups: Dict[str, List[str]]) -> Set[str]:
    """Get all files that are in valid groups."""
    files = set()
    for file_list in groups.values():
        files.update(file_list)
    return files


def generate_draft_yaml(
    case_dir: Path,
    groups: Dict[str, List[str]],
    standalone: List[str],
) -> Path:
    """
    Generate a draft document_groups.yaml for analyst review.

    Args:
        case_dir: Path to case directory
        groups: Detected groups {base_name: [files]}
        standalone: Files not in any group

    Returns:
        Path to generated YAML file
    """
    config = DocumentGroupsConfig(
        status="DRAFT",
        groups=[
            DocumentGroup(
                id=_sanitize_id(base_name),
                name=base_name,  # Analyst can improve this
                files=files,
            )
            for base_name, files in sorted(groups.items())
        ],
        standalone=standalone,
    )

    yaml_path = case_dir / "document_groups.yaml"

    # Build YAML content with comments
    yaml_content = _build_yaml_with_comments(config)

    yaml_path.write_text(yaml_content)
    logger.info(f"Generated draft document groups: {yaml_path}")

    return yaml_path


def _sanitize_id(name: str) -> str:
    """Convert a name to a valid ID."""
    # Replace spaces and special chars with underscores
    id_str = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    # Remove leading/trailing underscores
    id_str = id_str.strip("_")
    # Lowercase
    return id_str.lower()


def _build_yaml_with_comments(config: DocumentGroupsConfig) -> str:
    """Build YAML content with helpful comments."""
    lines = [
        "# Document Groupings - AUTO-GENERATED",
        "# ",
        "# Review this file before processing. Multi-part documents have been",
        "# detected based on filename patterns. Verify the groupings are correct.",
        "#",
        "# Instructions:",
        "#   1. Review each group - are these files really parts of one document?",
        "#   2. Edit 'name' fields to be human-readable (e.g., 'Escritura Publica No. 125')",
        "#   3. Add 'document_type' and 'date' if known",
        "#   4. Move any wrongly-grouped files to 'standalone'",
        "#   5. Change status from DRAFT to CONFIRMED when done",
        "#",
        "# Status: DRAFT means processing will be blocked until you confirm.",
        "#",
        "",
        f"status: {config.status}",
        "",
    ]

    if config.groups:
        lines.append("groups:")
        for group in config.groups:
            lines.append(f"  - id: {group.id}")
            lines.append(
                f'    name: "{group.name or group.id}"  # Edit this to be descriptive'
            )
            lines.append(
                "    # document_type:  # Optional: notarial_deed, registry_certificate, etc."
            )
            lines.append("    # date:  # Optional: YYYY-MM-DD")
            lines.append("    files:")
            for f in group.files:
                lines.append(f"      - {f}")
            lines.append("")
    else:
        lines.append("groups: []")
        lines.append("")

    if config.standalone:
        lines.append(
            "# Files not part of any group (processed as individual documents)"
        )
        lines.append("standalone:")
        for f in config.standalone:
            lines.append(f"  - {f}")
    else:
        lines.append("standalone: []")

    return "\n".join(lines) + "\n"


def load_document_groups(case_dir: Path) -> Optional[DocumentGroupsConfig]:
    """
    Load document groups configuration for a case.

    Args:
        case_dir: Path to case directory

    Returns:
        DocumentGroupsConfig if file exists, None otherwise
    """
    yaml_path = case_dir / "document_groups.yaml"

    if not yaml_path.exists():
        return None

    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        if data is None:
            return None

        config = DocumentGroupsConfig(**data)
        logger.info(
            f"Loaded document groups: {len(config.groups)} groups, "
            f"{len(config.standalone)} standalone, status={config.status}"
        )
        return config

    except Exception as e:
        logger.error(f"Failed to load document groups: {e}")
        raise ValueError(f"Invalid document_groups.yaml: {e}") from e


def validate_groups_against_files(
    config: DocumentGroupsConfig, actual_files: List[str]
) -> List[str]:
    """
    Validate that grouped files exist and no files are missing.

    Args:
        config: Document groups configuration
        actual_files: List of actual PDF files in the case

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    actual_set = set(actual_files)

    # Check that all grouped files exist
    for group in config.groups:
        for filename in group.files:
            if filename not in actual_set:
                errors.append(f"Group '{group.id}' references missing file: {filename}")

    # Check that all standalone files exist
    for filename in config.standalone:
        if filename not in actual_set:
            errors.append(f"Standalone list references missing file: {filename}")

    # Check for files not accounted for
    accounted_files = config.get_all_grouped_files() | set(config.standalone)
    unaccounted = actual_set - accounted_files
    if unaccounted:
        errors.append(f"Files not in groups or standalone list: {sorted(unaccounted)}")

    return errors
