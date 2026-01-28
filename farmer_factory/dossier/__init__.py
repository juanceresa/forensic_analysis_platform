"""Dossier generation module for forensic intelligence reports.

This module generates professional PDF dossiers from case data using:
- Pydantic models for data structure (models.py)
- DossierPreparer to assemble data from KnowledgeGraph (preparer.py)
- DossierRenderer to generate LaTeX via Jinja2 (renderer.py)
- DossierCompiler to compile LaTeX to PDF (compiler.py)

Usage:
    from farmer_factory.dossier import generate_dossier

    pdf_path = generate_dossier(
        case_id="TEST-CERESA",
        focal_property_id="property_abc123",
        focal_family_member_id="person_xyz789",
    )
"""

from pathlib import Path

from .models import (
    DossierData,
    DocumentSummary,
    EvidenceCitation,
    FamilyMember,
    FamilyTreeData,
    OwnershipPeriod,
    PropertyData,
    TimelineEvent,
    VerificationStats,
    STANDARD_DISCLAIMER,
)
from farmer_factory.utils import validate_case_id

__all__ = [
    "generate_dossier",
    "DossierData",
    "DocumentSummary",
    "EvidenceCitation",
    "FamilyMember",
    "FamilyTreeData",
    "OwnershipPeriod",
    "PropertyData",
    "TimelineEvent",
    "VerificationStats",
    "STANDARD_DISCLAIMER",
]


def generate_dossier(
    case_id: str,
    focal_property_id: str,
    focal_family_member_id: str,
    output_dir: Path | None = None,
    engine: str = "xelatex",
    dry_run: bool = False,
) -> Path:
    """Generate PDF dossier for a case.

    Args:
        case_id: Case identifier (e.g., "TEST-CERESA")
        focal_property_id: Entity ID of the property being claimed
        focal_family_member_id: Entity ID of primary claimant
        output_dir: Output directory (defaults to cases/{case_id}/output)
        engine: LaTeX engine to use ("xelatex" or "pdflatex")
        dry_run: If True, generate .tex but skip PDF compilation

    Returns:
        Path to generated PDF (or .tex if dry_run=True)

    Raises:
        ValueError: If case_id is invalid (prevents path traversal)
    """
    # Validate case_id to prevent path traversal
    if not validate_case_id(case_id):
        raise ValueError(f"Invalid case_id: {case_id}")

    # Import here to avoid circular imports
    from .preparer import DossierPreparer
    from .renderer import DossierRenderer
    from .compiler import DossierCompiler

    output_dir = output_dir or Path(f"cases/{case_id}/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare data
    preparer = DossierPreparer(case_id)
    data = preparer.prepare(focal_property_id, focal_family_member_id)

    # 2. Render to LaTeX
    renderer = DossierRenderer()
    tex_path = renderer.render(data, output_dir)

    if dry_run:
        return tex_path

    # 3. Compile to PDF
    compiler = DossierCompiler(engine=engine)
    pdf_path = compiler.compile(tex_path, output_dir)

    return pdf_path
