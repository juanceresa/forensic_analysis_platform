"""Integration test for full intake workflow."""

import pytest
import fitz
from pathlib import Path
from farmer_factory.intake import (
    DocumentGrouper,
    PDFLoader,
    ProvenanceTracker,
    ManifestManager
)


def test_full_intake_workflow(tmp_path):
    """Test complete intake workflow with multi-part documents."""
    # Setup: Create test PDFs
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Document 1: Single file
    pdf1 = input_dir / "will.pdf"
    doc = fitz.open()
    for i in range(2):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Will page {i+1}")
    doc.save(pdf1)
    doc.close()

    # Document 2: Multi-part
    pdf2a = input_dir / "deed.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Deed part 1")
    doc.save(pdf2a)
    doc.close()

    pdf2b = input_dir / "deed.1pdf.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Deed part 2")
    doc.save(pdf2b)
    doc.close()

    # Initialize components
    grouper = DocumentGrouper()
    loader = PDFLoader(dpi=150)
    provenance_tracker = ProvenanceTracker()
    manifest = ManifestManager(case_id="TEST-001")

    output_dir = tmp_path / "output"

    # Find and group PDFs
    pdf_files = list(input_dir.glob("*.pdf"))
    assert len(pdf_files) == 3

    document_groups = grouper.group_documents(pdf_files)
    assert len(document_groups) == 2  # "will" and "deed"

    # Process each document group
    for doc_id, (base_name, pdf_parts) in enumerate(sorted(document_groups.items()), start=1):
        document_id = f"DOC-{doc_id:03d}"

        # Extract pages
        page_paths = loader.load_document_group(
            pdf_parts,
            output_dir / "raw_images" / document_id
        )

        # Create provenance
        provenance = provenance_tracker.create_provenance(
            document_id, pdf_parts, len(page_paths), "success"
        )
        provenance_tracker.save_provenance(
            provenance,
            output_dir / "intake" / "provenance" / f"{document_id}_provenance.json"
        )

        # Update manifest
        manifest.add_document(
            document_id, base_name, "success",
            len(pdf_parts), len(page_paths)
        )

    # Save manifest
    manifest.save_manifest(output_dir / "intake" / "manifest.json")

    # Verify output structure
    assert (output_dir / "intake" / "manifest.json").exists()
    assert (output_dir / "intake" / "provenance" / "DOC-001_provenance.json").exists()
    assert (output_dir / "intake" / "provenance" / "DOC-002_provenance.json").exists()

    # Verify images
    assert (output_dir / "raw_images" / "DOC-001" / "page_001.png").exists()
    assert (output_dir / "raw_images" / "DOC-001" / "page_002.png").exists()
    assert (output_dir / "raw_images" / "DOC-002" / "page_001.png").exists()
    assert (output_dir / "raw_images" / "DOC-002" / "page_002.png").exists()

    # Verify manifest
    summary = manifest.get_summary()
    assert summary["total_documents"] == 2
    assert summary["successful"] == 2
    assert summary["failed"] == 0
