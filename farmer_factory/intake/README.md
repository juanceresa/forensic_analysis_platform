# Intake Module

Document intake and initial processing module for the Civic Table Forensic Intelligence platform.

## Overview

The intake module handles the first stage of the document processing pipeline:

1. **PDF Loading**: Extract page images from PDF documents at configurable DPI
2. **Multi-part Grouping**: Automatically group document parts (e.g., `will.pdf`, `will.1pdf.pdf`)
3. **Provenance Tracking**: Create immutable chain-of-custody metadata with SHA-256 hashes
4. **Manifest Generation**: Batch processing logs with success/failure tracking

## Components

### DocumentGrouper

Groups multi-part PDF files into logical documents based on filename patterns.

**Supported patterns:**
- `.1pdf.pdf`, `.2pdf.pdf` (e.g., `deed.1pdf.pdf`)
- `_part1.pdf`, `_part2.pdf` (e.g., `deed_part1.pdf`)
- `(1).pdf`, `(2).pdf` (e.g., `deed (1).pdf`)
- `-1.pdf`, `-2.pdf` (e.g., `deed-1.pdf`)

**Example:**
```python
from farmer_factory.intake import DocumentGrouper
from pathlib import Path

grouper = DocumentGrouper()
pdf_files = list(Path("input/CASE-001/documents").glob("*.pdf"))

# Returns: {"deed": [deed.pdf, deed.1pdf.pdf], "will": [will.pdf]}
document_groups = grouper.group_documents(pdf_files)
```

### PDFLoader

Extracts page images from PDF documents at configurable DPI (default 300).

**Features:**
- Configurable DPI for extraction quality
- Sequential page numbering across multi-part documents
- Automatic output directory creation
- Memory-efficient page-by-page processing

**Example:**
```python
from farmer_factory.intake import PDFLoader
from pathlib import Path

loader = PDFLoader(dpi=300)

# Single document
page_paths = loader.load_document_group(
    [Path("input/deed.pdf")],
    Path("output/raw_images/DOC-001")
)
# Returns: [page_001.png, page_002.png, ...]

# Multi-part document
page_paths = loader.load_document_group(
    [Path("input/deed.pdf"), Path("input/deed.1pdf.pdf")],
    Path("output/raw_images/DOC-002")
)
# Returns: [page_001.png, page_002.png, page_003.png, ...]
# Pages numbered sequentially across all parts
```

### ProvenanceTracker

Creates provenance metadata for chain-of-custody audit trails.

**Metadata includes:**
- Document ID
- Original filename (base name without multi-part suffix)
- Source file list with SHA-256 hashes
- File sizes
- Total page count
- Intake timestamp (ISO 8601 with 'Z' suffix)
- Extraction DPI
- Status (success/failed)
- Missing parts (if applicable)

**Example:**
```python
from farmer_factory.intake import ProvenanceTracker
from pathlib import Path

tracker = ProvenanceTracker()

provenance = tracker.create_provenance(
    document_id="DOC-001",
    pdf_parts=[Path("input/deed.pdf"), Path("input/deed.1pdf.pdf")],
    page_count=8,
    status="success"
)

tracker.save_provenance(
    provenance,
    Path("output/intake/provenance/DOC-001_provenance.json")
)
```

**Provenance JSON structure:**
```json
{
  "document_id": "DOC-001",
  "original_filename": "deed",
  "part_count": 2,
  "source_files": [
    {
      "filename": "deed.pdf",
      "file_hash": "sha256:abc123...",
      "file_size_bytes": 245760,
      "pages_in_part": 0
    },
    {
      "filename": "deed.1pdf.pdf",
      "file_hash": "sha256:def456...",
      "file_size_bytes": 189440,
      "pages_in_part": 0
    }
  ],
  "total_page_count": 8,
  "intake_timestamp": "2026-01-22T13:45:00.123456Z",
  "extraction_dpi": 300,
  "status": "success",
  "missing_parts": []
}
```

### ManifestManager

Manages batch intake manifests with document-level status tracking.

**Features:**
- Document-level status tracking (success/failed/skipped)
- Aggregate statistics (total, successful, failed, skipped counts)
- Optional error messages for failed documents
- ISO 8601 timestamps

**Example:**
```python
from farmer_factory.intake import ManifestManager
from pathlib import Path

manifest = ManifestManager(case_id="CASE-001")

# Add documents as they're processed
manifest.add_document(
    document_id="DOC-001",
    filename="deed",
    status="success",
    part_count=2,
    page_count=8
)

manifest.add_document(
    document_id="DOC-002",
    filename="corrupted_will",
    status="failed",
    part_count=0,
    page_count=0,
    error="PDF corrupted: unable to open"
)

# Save manifest with summary
manifest.save_manifest(Path("output/intake/manifest.json"))

# Get summary statistics
summary = manifest.get_summary()
# Returns: {"total_documents": 2, "successful": 1, "failed": 1, "skipped": 0}
```

**Manifest JSON structure:**
```json
{
  "case_id": "CASE-001",
  "intake_timestamp": "2026-01-22T13:45:00.123456Z",
  "total_documents": 2,
  "successful": 1,
  "failed": 1,
  "skipped": 0,
  "documents": [
    {
      "document_id": "DOC-001",
      "filename": "deed",
      "status": "success",
      "part_count": 2,
      "page_count": 8
    },
    {
      "document_id": "DOC-002",
      "filename": "corrupted_will",
      "status": "failed",
      "part_count": 0,
      "page_count": 0,
      "error": "PDF corrupted: unable to open"
    }
  ]
}
```

## Full Workflow Example

```python
from pathlib import Path
from farmer_factory.intake import (
    DocumentGrouper,
    PDFLoader,
    ProvenanceTracker,
    ManifestManager
)

# Setup
input_dir = Path("input/CASE-001/documents")
output_dir = Path("output/CASE-001")

grouper = DocumentGrouper()
loader = PDFLoader(dpi=300)
tracker = ProvenanceTracker()
manifest = ManifestManager(case_id="CASE-001")

# Find and group PDFs
pdf_files = list(input_dir.glob("*.pdf"))
document_groups = grouper.group_documents(pdf_files)

# Process each document group
for doc_id, (base_name, pdf_parts) in enumerate(sorted(document_groups.items()), start=1):
    document_id = f"DOC-{doc_id:03d}"

    try:
        # Extract pages
        page_paths = loader.load_document_group(
            pdf_parts,
            output_dir / "raw_images" / document_id
        )

        # Create provenance
        provenance = tracker.create_provenance(
            document_id, pdf_parts, len(page_paths), "success"
        )
        tracker.save_provenance(
            provenance,
            output_dir / "intake" / "provenance" / f"{document_id}_provenance.json"
        )

        # Update manifest
        manifest.add_document(
            document_id, base_name, "success",
            len(pdf_parts), len(page_paths)
        )

    except Exception as e:
        # Handle errors
        manifest.add_document(
            document_id, base_name, "failed",
            0, 0, error=str(e)
        )

# Save manifest
manifest.save_manifest(output_dir / "intake" / "manifest.json")

# Print summary
summary = manifest.get_summary()
print(f"Processed {summary['total_documents']} documents")
print(f"  Successful: {summary['successful']}")
print(f"  Failed: {summary['failed']}")
```

## Output Structure

```
output/CASE-001/
├── intake/
│   ├── manifest.json
│   └── provenance/
│       ├── DOC-001_provenance.json
│       ├── DOC-002_provenance.json
│       └── ...
└── raw_images/
    ├── DOC-001/
    │   ├── page_001.png
    │   ├── page_002.png
    │   └── ...
    ├── DOC-002/
    │   ├── page_001.png
    │   └── ...
    └── ...
```

## Error Handling

### PDFLoadError

Raised when PDF loading fails:
- Corrupted PDF files
- Password-protected PDFs
- Invalid file format
- Disk space issues

**Example:**
```python
from farmer_factory.intake import PDFLoader, PDFLoadError

loader = PDFLoader()
try:
    pages = loader.load_document_group(
        [Path("corrupted.pdf")],
        Path("output/images")
    )
except PDFLoadError as e:
    print(f"Failed to load PDF: {e}")
```

## Multi-part Document Handling

The intake module automatically handles documents split across multiple PDF files:

1. **Detection**: DocumentGrouper scans filenames for multi-part patterns
2. **Grouping**: Files with the same base name are grouped together
3. **Sorting**: Parts are sorted by part number (e.g., part 1 before part 2)
4. **Sequential Numbering**: PDFLoader numbers pages consecutively across all parts
5. **Provenance**: All source files are recorded in provenance metadata

**Example filenames:**
- `deed.pdf` + `deed.1pdf.pdf` → grouped as "deed"
- `will_part1.pdf` + `will_part2.pdf` → grouped as "will"
- `contract (1).pdf` + `contract (2).pdf` → grouped as "contract"

## Dependencies

- **PyMuPDF (fitz)**: PDF parsing and rendering
- **hashlib**: SHA-256 hash computation (stdlib)
- **pathlib**: File path handling (stdlib)
- **json**: JSON serialization (stdlib)
- **datetime**: Timestamp generation (stdlib)

## Testing

Run the intake module test suite:

```bash
pytest tests/intake/ -v
```

Test coverage includes:
- Document grouping with various filename patterns
- Single-page and multi-page PDF extraction
- Multi-part document handling
- Provenance generation and hash computation
- Manifest creation and summary calculation
- End-to-end integration workflow
