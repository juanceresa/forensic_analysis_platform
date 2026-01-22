# CLI Pipeline Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect prepare → extract → structure modules through a working `process` command that converts PDFs to knowledge graphs.

**Architecture:** Pipeline processes PDFs sequentially: PDF → images → preprocess → extract → graph → JSON. Stop on first error. Save all intermediate outputs for debugging.

**Tech Stack:** pdf2image (PDF conversion), existing prepare/extract/structure modules, Click (CLI), cv2 (image I/O), logging, JSON

---

## Task 1: Add pdf2image Dependency

**Files:**
- Modify: `farmer_factory/requirements.txt:15`

**Step 1: Add pdf2image to requirements.txt**

Add this line after PyMuPDF (line 15):

```txt
pdf2image>=1.16.0  # PDF to image conversion
```

**Step 2: Verify no conflicts**

Run: `grep -i pdf farmer_factory/requirements.txt`
Expected: See both PyMuPDF and pdf2image listed

**Step 3: Commit**

```bash
git add farmer_factory/requirements.txt
git commit -m "feat: add pdf2image dependency for PDF to image conversion"
```

---

## Task 2: Create Processing Module with Helper Functions

**Files:**
- Create: `farmer_factory/processing/__init__.py`
- Create: `farmer_factory/processing/helpers.py`
- Test: `tests/processing/test_helpers.py`

**Step 1: Write test for load_pdf_pages**

Create `tests/processing/test_helpers.py`:

```python
"""Unit tests for processing helper functions."""

import pytest
from pathlib import Path
from farmer_factory.processing.helpers import load_pdf_pages


def test_load_pdf_pages_single_page(tmp_path):
    """Test PDF to image conversion with single page PDF."""
    # Note: This test requires a real PDF file
    # We'll use the sample PDF from farmer_factory/sample_docs/
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # Verify we got at least one page
    assert len(page_paths) > 0

    # Verify all pages exist and are PNGs
    for path in page_paths:
        assert path.exists()
        assert path.suffix == ".png"
        # Verify naming pattern
        assert path.stem.startswith(sample_pdf.stem)
        assert "_page_" in path.stem


def test_load_pdf_pages_creates_files(tmp_path):
    """Test that load_pdf_pages saves images to disk."""
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # Verify files were actually written
    for path in page_paths:
        # Check file size > 0 (not empty)
        assert path.stat().st_size > 0


def test_load_pdf_pages_naming_convention(tmp_path):
    """Test document ID naming convention."""
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")

    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    output_dir = tmp_path / "preprocessed"
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    # First page should be {stem}_page_0.png
    first_page = page_paths[0]
    expected_stem = f"{sample_pdf.stem}_page_0"
    assert first_page.stem == expected_stem
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/processing/test_helpers.py::test_load_pdf_pages_single_page -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'farmer_factory.processing'"

**Step 3: Create processing module structure**

Create `farmer_factory/processing/__init__.py`:

```python
"""
Processing module.
Handles PDF loading, pipeline orchestration, and helper utilities.
"""

from .helpers import load_pdf_pages, save_extraction_json, setup_logging

__all__ = [
    "load_pdf_pages",
    "save_extraction_json",
    "setup_logging",
]
```

**Step 4: Run test to verify new error**

Run: `pytest tests/processing/test_helpers.py::test_load_pdf_pages_single_page -v`
Expected: FAIL with "cannot import name 'load_pdf_pages'"

**Step 5: Implement load_pdf_pages**

Create `farmer_factory/processing/helpers.py`:

```python
"""Helper functions for document processing pipeline."""

import json
import logging
from pathlib import Path
from typing import List
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


def load_pdf_pages(pdf_path: Path, output_dir: Path) -> List[Path]:
    """
    Convert PDF to images, one per page.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images

    Returns:
        List of paths to saved page images

    Raises:
        ValueError: If PDF cannot be converted
    """
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,              # High quality for OCR
            grayscale=True,       # Matches prepare module expectations
            fmt='png'
        )
    except Exception as e:
        raise ValueError(f"Failed to convert PDF {pdf_path.name}: {e}")

    page_paths = []
    for i, image in enumerate(images):
        page_path = output_dir / f"{pdf_path.stem}_page_{i}.png"
        image.save(page_path, 'PNG')
        page_paths.append(page_path)
        logger.debug(f"Saved page {i} to {page_path}")

    logger.info(f"Converted {pdf_path.name} to {len(page_paths)} images")
    return page_paths


def save_extraction_json(extraction, output_path: Path) -> None:
    """
    Save extraction result to JSON with proper serialization.

    Args:
        extraction: ExtractionResult object
        output_path: Path to save JSON file
    """
    from datetime import datetime

    class DateTimeEncoder(json.JSONEncoder):
        """Custom JSON encoder for datetime objects."""
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    data = {
        'entities': [e.model_dump() for e in extraction.entities],
        'relations': [r.model_dump() for r in extraction.relations],
        'confidence_scores': extraction.confidence_scores,
        'path': extraction.path.value,
        'processing_metadata': extraction.processing_metadata
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    logger.debug(f"Saved extraction to {output_path}")


def setup_logging(log_file: Path) -> None:
    """
    Configure dual logging: file (DEBUG) + console (INFO).

    Args:
        log_file: Path to log file
    """
    # Create log directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler: detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler: user-facing info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"Logging configured: {log_file}")
```

**Step 6: Create test directory**

Run: `mkdir -p tests/processing`

**Step 7: Create test __init__.py**

Run: `touch tests/processing/__init__.py`

**Step 8: Run tests to verify they pass**

Run: `pytest tests/processing/test_helpers.py -v`
Expected: PASS (all 3 tests)

**Step 9: Commit**

```bash
git add farmer_factory/processing/ tests/processing/
git commit -m "feat: add PDF loading and helper functions for processing pipeline"
```

---

## Task 3: Create ProcessingError Exception

**Files:**
- Create: `farmer_factory/processing/exceptions.py`
- Modify: `farmer_factory/processing/__init__.py:3`
- Test: `tests/processing/test_exceptions.py`

**Step 1: Write test for ProcessingError**

Create `tests/processing/test_exceptions.py`:

```python
"""Unit tests for processing exceptions."""

import pytest
from farmer_factory.processing.exceptions import ProcessingError


def test_processing_error_basic():
    """Test ProcessingError can be raised and caught."""
    with pytest.raises(ProcessingError) as exc_info:
        raise ProcessingError("Test error message")

    assert str(exc_info.value) == "Test error message"


def test_processing_error_with_context():
    """Test ProcessingError with contextual information."""
    document_id = "test_doc_page_0"
    stage = "preprocessing"

    error_msg = f"Failed {stage} for {document_id}: Image corrupted"

    with pytest.raises(ProcessingError) as exc_info:
        raise ProcessingError(error_msg)

    assert document_id in str(exc_info.value)
    assert stage in str(exc_info.value)


def test_processing_error_inherits_exception():
    """Test ProcessingError is a proper Exception."""
    error = ProcessingError("Test")
    assert isinstance(error, Exception)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/processing/test_exceptions.py::test_processing_error_basic -v`
Expected: FAIL with "cannot import name 'ProcessingError'"

**Step 3: Implement ProcessingError**

Create `farmer_factory/processing/exceptions.py`:

```python
"""Custom exceptions for processing pipeline."""


class ProcessingError(Exception):
    """
    Exception raised when document processing fails.

    Used to wrap errors from PDF loading, preprocessing, extraction,
    or graph building stages. Provides clear context about which
    document/stage failed for better error reporting.
    """
    pass
```

**Step 4: Update processing __init__.py**

Modify `farmer_factory/processing/__init__.py`:

```python
"""
Processing module.
Handles PDF loading, pipeline orchestration, and helper utilities.
"""

from .helpers import load_pdf_pages, save_extraction_json, setup_logging
from .exceptions import ProcessingError

__all__ = [
    "load_pdf_pages",
    "save_extraction_json",
    "setup_logging",
    "ProcessingError",
]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/processing/test_exceptions.py -v`
Expected: PASS (all 3 tests)

**Step 6: Commit**

```bash
git add farmer_factory/processing/exceptions.py farmer_factory/processing/__init__.py tests/processing/test_exceptions.py
git commit -m "feat: add ProcessingError exception for pipeline errors"
```

---

## Task 4: Implement Core process_case Function

**Files:**
- Create: `farmer_factory/processing/pipeline.py`
- Modify: `farmer_factory/processing/__init__.py:4`
- Test: `tests/processing/test_pipeline.py`

**Step 1: Write integration test for process_case**

Create `tests/processing/test_pipeline.py`:

```python
"""Integration tests for processing pipeline."""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from farmer_factory.processing.pipeline import process_case
from farmer_factory.processing.exceptions import ProcessingError


def test_process_case_end_to_end(tmp_path):
    """Test full pipeline with real sample PDF."""
    # Setup test case directory
    cases_dir = tmp_path / "cases"
    case_id = "TEST-001"
    case_dir = cases_dir / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)

    # Copy sample PDF
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")
    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    shutil.copy(sample_pdf, intake_dir)

    # Create metadata
    metadata = {
        'id': case_id,
        'name': 'Test Case',
        'family': 'Test',
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create other required directories
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Run processing (with tmp_path as base)
    stats = process_case(case_id, base_dir=cases_dir)

    # Verify statistics returned
    assert stats['documents_processed'] > 0
    assert stats['entities_extracted'] >= 0
    assert stats['entities_merged'] >= 0
    assert stats['relations_added'] >= 0

    # Verify outputs exist
    assert (case_dir / 'output' / 'graph_data.json').exists()
    assert (case_dir / 'processing.log').exists()

    # Verify graph structure
    with open(case_dir / 'output' / 'graph_data.json') as f:
        graph = json.load(f)

    assert 'nodes' in graph
    assert 'links' in graph
    assert 'metadata' in graph
    assert graph['metadata']['case_id'] == case_id


def test_process_case_missing_case_dir(tmp_path):
    """Test error handling when case directory doesn't exist."""
    cases_dir = tmp_path / "cases"

    with pytest.raises(ProcessingError) as exc_info:
        process_case("NONEXISTENT", base_dir=cases_dir)

    assert "not found" in str(exc_info.value).lower()


def test_process_case_no_pdfs(tmp_path):
    """Test handling of case with no PDFs in intake."""
    cases_dir = tmp_path / "cases"
    case_id = "EMPTY-001"
    case_dir = cases_dir / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Should complete successfully but process 0 documents
    stats = process_case(case_id, base_dir=cases_dir)

    assert stats['documents_processed'] == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/processing/test_pipeline.py::test_process_case_end_to_end -v`
Expected: FAIL with "cannot import name 'process_case'"

**Step 3: Implement process_case function**

Create `farmer_factory/processing/pipeline.py`:

```python
"""Main processing pipeline orchestration."""

import logging
import cv2
from pathlib import Path
from typing import Dict, Any

from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import (
    ExtractionPipeline,
    OCRService,
    VisionExtractionService,
    LLMExtractionService,
    SchemaValidator
)
from farmer_factory.structure import (
    KnowledgeGraph,
    EntityResolver,
    GraphBuilder,
    GraphExporter
)
from .helpers import load_pdf_pages, save_extraction_json, setup_logging
from .exceptions import ProcessingError

logger = logging.getLogger(__name__)


def process_case(case_id: str, base_dir: Path = None) -> Dict[str, Any]:
    """
    Process all PDFs in case through complete pipeline.

    Pipeline stages:
    1. PDF Loading - Convert PDFs to images using pdf2image
    2. Preprocessing - Deskew, denoise, triage (prepare module)
    3. Extraction - OCR + Vision + LLM entity/relation extraction
    4. Graph Building - Entity deduplication, graph construction
    5. Export - Save graph_data.json in force-graph format

    Args:
        case_id: Case identifier (e.g., "CASE-CERESA")
        base_dir: Base directory for cases (defaults to "cases")

    Returns:
        Dictionary with processing statistics

    Raises:
        ProcessingError: If any stage fails
    """
    if base_dir is None:
        base_dir = Path('cases')

    # 1. Setup paths and logging
    case_dir = base_dir / case_id
    if not case_dir.exists():
        raise ProcessingError(f"Case directory not found: {case_dir}")

    intake_dir = case_dir / 'intake'
    preprocessed_dir = case_dir / 'preprocessed'
    extractions_dir = case_dir / 'extractions'
    output_dir = case_dir / 'output'

    # Ensure output directories exist
    preprocessed_dir.mkdir(parents=True, exist_ok=True)
    extractions_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(case_dir / 'processing.log')
    logger.info(f"Starting processing for case: {case_id}")

    # 2. Initialize pipelines once (reuse across all documents)
    logger.info("Initializing pipelines...")
    try:
        prep_pipeline = PreprocessingPipeline()
        extract_pipeline = ExtractionPipeline(
            ocr_service=OCRService(),
            vision_service=VisionExtractionService(),
            llm_service=LLMExtractionService(),
            validator=SchemaValidator()
        )
    except Exception as e:
        raise ProcessingError(f"Failed to initialize pipelines: {e}")

    # 3. Initialize graph builder
    logger.info("Initializing graph builder...")
    try:
        graph = KnowledgeGraph(case_id=case_id)
        resolver = EntityResolver(similarity_threshold=0.85)
        builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)
    except Exception as e:
        raise ProcessingError(f"Failed to initialize graph builder: {e}")

    # 4. Process each PDF
    pdfs = sorted(intake_dir.glob('*.pdf'))
    logger.info(f"Found {len(pdfs)} PDFs to process")

    for pdf_idx, pdf_path in enumerate(pdfs, 1):
        logger.info(f"[{pdf_idx}/{len(pdfs)}] Processing {pdf_path.name}...")

        # Convert PDF to images
        try:
            page_images = load_pdf_pages(pdf_path, preprocessed_dir)
            logger.info(f"  Loaded {len(page_images)} pages")
        except Exception as e:
            raise ProcessingError(f"Failed to load PDF {pdf_path.name}: {e}")

        # Process each page
        for page_idx, page_path in enumerate(page_images, 1):
            logger.info(f"  Page {page_idx}/{len(page_images)}...")

            # Preprocess
            try:
                raw_image = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
                if raw_image is None:
                    raise ValueError(f"Failed to load image: {page_path}")
                preprocessed = prep_pipeline.process_page(raw_image)
            except Exception as e:
                raise ProcessingError(f"Failed preprocessing {page_path.name}: {e}")

            # Save preprocessed image
            try:
                preprocessed_path = preprocessed_dir / f"{page_path.stem}_processed.png"
                cv2.imwrite(str(preprocessed_path), preprocessed.image)
            except Exception as e:
                logger.warning(f"Failed to save preprocessed image: {e}")

            # Extract entities
            try:
                document_id = page_path.stem
                extraction = extract_pipeline.extract_page(preprocessed, document_id=document_id)
            except Exception as e:
                raise ProcessingError(f"Failed extraction {page_path.stem}: {e}")

            # Save extraction JSON
            try:
                extraction_path = extractions_dir / f"{document_id}.json"
                save_extraction_json(extraction, extraction_path)
            except Exception as e:
                logger.warning(f"Failed to save extraction JSON: {e}")

            # Add to graph (with auto-deduplication)
            try:
                builder.add_extraction(extraction)
            except Exception as e:
                raise ProcessingError(f"Failed adding to graph {document_id}: {e}")

            logger.info(f"  Page {page_idx}/{len(page_images)} ✓")

    # 5. Export graph
    logger.info("Exporting graph...")
    try:
        exporter = GraphExporter(knowledge_graph=graph)
        exporter.save(output_dir / 'graph_data.json', factory_version="1.0.0")
    except Exception as e:
        raise ProcessingError(f"Failed to export graph: {e}")

    # 6. Get summary statistics
    stats = builder.processing_stats
    logger.info("Processing complete!")
    logger.info(f"Documents processed: {stats['documents_processed']}")
    logger.info(f"Entities extracted:  {stats['entities_extracted']}")
    logger.info(f"Entities merged:     {stats['entities_merged']}")
    logger.info(f"Relations added:     {stats['relations_added']}")

    return stats
```

**Step 4: Update processing __init__.py**

Modify `farmer_factory/processing/__init__.py`:

```python
"""
Processing module.
Handles PDF loading, pipeline orchestration, and helper utilities.
"""

from .helpers import load_pdf_pages, save_extraction_json, setup_logging
from .exceptions import ProcessingError
from .pipeline import process_case

__all__ = [
    "load_pdf_pages",
    "save_extraction_json",
    "setup_logging",
    "ProcessingError",
    "process_case",
]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/processing/test_pipeline.py -v -s`
Expected: PASS (all 3 tests) - Note: This will take longer as it processes real PDFs

**Step 6: Commit**

```bash
git add farmer_factory/processing/pipeline.py farmer_factory/processing/__init__.py tests/processing/test_pipeline.py
git commit -m "feat: implement core process_case pipeline function"
```

---

## Task 5: Update CLI Process Command

**Files:**
- Modify: `farmer_factory/cli.py:69-93`

**Step 1: Write CLI integration test**

Create `tests/test_cli_integration.py`:

```python
"""CLI integration tests."""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from farmer_factory.cli import cli


def test_cli_process_command(tmp_path):
    """Test CLI process command end-to-end."""
    # Setup test case
    case_id = "TEST-CLI-001"
    case_dir = tmp_path / "cases" / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)

    # Copy sample PDF
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")
    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    shutil.copy(sample_pdf, intake_dir)

    # Create metadata
    metadata = {
        'id': case_id,
        'name': 'Test Case',
        'family': 'Test',
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create required directories
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Run CLI command (change to tmp_path first)
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ['process', case_id])

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify output message
        assert "Processing Complete!" in result.output
        assert "Graph saved to:" in result.output

    finally:
        os.chdir(original_dir)

    # Verify outputs exist
    assert (case_dir / 'output' / 'graph_data.json').exists()
    assert (case_dir / 'processing.log').exists()


def test_cli_process_nonexistent_case(tmp_path):
    """Test CLI error handling for nonexistent case."""
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ['process', 'NONEXISTENT'])

        # Should fail with error
        assert result.exit_code != 0
        assert "Processing failed" in result.output or "not found" in result.output

    finally:
        os.chdir(original_dir)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_integration.py::test_cli_process_command -v`
Expected: FAIL - CLI shows "Processing pipeline not yet implemented"

**Step 3: Update CLI process command**

Modify `farmer_factory/cli.py` (lines 69-93):

```python
@cli.command()
@click.argument('case_id')
@click.option('--verbose', is_flag=True, help='Verbose output')
def process(case_id: str, verbose: bool):
    """Process case documents through the pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Processing case: {case_id}")

    # Import here to avoid circular imports
    from farmer_factory.processing import process_case, ProcessingError

    try:
        # Run processing pipeline
        stats = process_case(case_id)

        # Print summary
        click.echo("\n" + "="*60)
        click.echo("Processing Complete!")
        click.echo("="*60)
        click.echo(f"Documents processed: {stats['documents_processed']}")
        click.echo(f"Entities extracted:  {stats['entities_extracted']}")
        click.echo(f"Entities merged:     {stats['entities_merged']}")
        click.echo(f"Relations added:     {stats['relations_added']}")

        output_path = Path('cases') / case_id / 'output' / 'graph_data.json'
        click.echo(f"\nGraph saved to: {output_path}")

    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"\n❌ Processing failed: {e}", err=True)
        case_dir = Path('cases') / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        case_dir = Path('cases') / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_integration.py::test_cli_process_command -v -s`
Expected: PASS

**Step 5: Test error handling**

Run: `pytest tests/test_cli_integration.py::test_cli_process_nonexistent_case -v`
Expected: PASS

**Step 6: Commit**

```bash
git add farmer_factory/cli.py tests/test_cli_integration.py
git commit -m "feat: connect process command to pipeline implementation"
```

---

## Task 6: Manual End-to-End Testing

**Files:**
- None (manual testing only)

**Step 1: Install system dependencies**

Run: `brew install poppler` (macOS)
Expected: Poppler installed successfully

**Step 2: Install Python dependencies**

Run: `pip install -r farmer_factory/requirements.txt`
Expected: All packages installed, including pdf2image

**Step 3: Create test case**

Run: `python farmer_factory/cli.py create-case --id TEST-CERESA --name "Ceresa Test" --family "Ceresa"`
Expected: Case created with directory structure

**Step 4: Copy sample PDFs**

Run: `cp "farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf" cases/TEST-CERESA/intake/`
Expected: PDF copied to intake directory

**Step 5: Run processing**

Run: `python farmer_factory/cli.py process TEST-CERESA --verbose`
Expected:
- Progress messages for each page
- "Processing Complete!" message
- Statistics showing entities extracted, merged, relations added

**Step 6: Verify outputs**

Run: `ls -la cases/TEST-CERESA/preprocessed/`
Expected: PNG files for each page (e.g., `1960 5 13 Mario Ceresa Co Heir Doc_page_0.png`)

Run: `ls -la cases/TEST-CERESA/extractions/`
Expected: JSON files for each page (e.g., `1960 5 13 Mario Ceresa Co Heir Doc_page_0.json`)

Run: `ls -la cases/TEST-CERESA/output/`
Expected: `graph_data.json` file exists

**Step 7: Inspect graph structure**

Run: `cat cases/TEST-CERESA/output/graph_data.json | jq '.metadata'`
Expected: Metadata showing case_id, entity_count, relation_count, factory_version

Run: `cat cases/TEST-CERESA/output/graph_data.json | jq '.nodes | length'`
Expected: Number of nodes (entities) extracted

Run: `cat cases/TEST-CERESA/output/graph_data.json | jq '.links | length'`
Expected: Number of links (relations) extracted

**Step 8: Check logs**

Run: `tail -50 cases/TEST-CERESA/processing.log`
Expected: Detailed log entries showing each processing stage

**Step 9: Test error handling**

Run: `python farmer_factory/cli.py process NONEXISTENT-CASE`
Expected: Error message "Case directory not found" and non-zero exit code

**Step 10: Document results**

Create `docs/manual-testing-results.md` summarizing:
- Test date
- Sample PDFs used
- Number of pages processed
- Entities/relations extracted
- Any issues encountered

---

## Task 7: Update Documentation

**Files:**
- Create: `docs/CLI_USAGE.md`
- Modify: `README.md` (if exists)

**Step 1: Create CLI usage documentation**

Create `docs/CLI_USAGE.md`:

```markdown
# CLI Usage Guide

## Installation

### System Dependencies

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
Download poppler binaries from: https://github.com/oschwartz10612/poppler-windows/releases
Add to PATH.

### Python Dependencies

```bash
pip install -r farmer_factory/requirements.txt
```

## Commands

### Create a New Case

```bash
python farmer_factory/cli.py create-case --id CASE-CERESA --name "Ceresa Family Archive" --family "Ceresa"
```

Creates case directory structure:
```
cases/CASE-CERESA/
  intake/          # Place PDFs here
  preprocessed/    # Auto-generated images
  extractions/     # Auto-generated JSON
  output/          # Final graph_data.json
  metadata.json    # Case information
```

### Process Documents

```bash
# Process all PDFs in case
python farmer_factory/cli.py process CASE-CERESA

# Verbose output for debugging
python farmer_factory/cli.py process CASE-CERESA --verbose
```

**What happens:**
1. PDFs converted to images (300 DPI grayscale)
2. Images preprocessed (deskew, denoise, triage)
3. Entities/relations extracted (OCR + Vision + LLM)
4. Knowledge graph built (auto-deduplication)
5. Graph exported to `graph_data.json`

**Output:**
```
[1/3] Processing 1960_Mario_Ceresa.pdf...
  Loaded 2 pages
  Page 1/2... ✓
  Page 2/2... ✓

============================================================
Processing Complete!
============================================================
Documents processed: 3
Entities extracted:  47
Entities merged:     12
Relations added:     23

Graph saved to: cases/CASE-CERESA/output/graph_data.json
```

### List Cases

```bash
python farmer_factory/cli.py list-cases
```

Shows all cases with status.

## Troubleshooting

### "poppler not found"
Install poppler (see system dependencies above).

### Processing fails on specific PDF
Check `cases/CASE-ID/processing.log` for detailed error messages.

### Low entity extraction
- Verify PDF quality (scanned vs digital)
- Check OCR confidence in extraction JSONs
- Review `processing.log` for warnings

## File Formats

### Intermediate Outputs

**Preprocessed Images:** `cases/CASE-ID/preprocessed/{pdf_stem}_page_{n}.png`
- 300 DPI grayscale PNG
- Deskewed and denoised

**Extraction JSON:** `cases/CASE-ID/extractions/{pdf_stem}_page_{n}.json`
- Entities with TIER_3_AI verification
- Relations with confidence scores
- OCR text and metadata

### Final Output

**Graph Data:** `cases/CASE-ID/output/graph_data.json`
- Force-graph format (nodes + links)
- Ready for frontend consumption
- All entities with verification tiers

## Next Steps

After processing:
1. Review graph in frontend (The Vault)
2. Analyst verification (promote TIER_3_AI → TIER_2_ANALYST)
3. Upload to Supabase (coming soon)
```

**Step 2: Commit documentation**

```bash
git add docs/CLI_USAGE.md
git commit -m "docs: add CLI usage guide"
```

---

## Success Criteria

After completing all tasks:

✅ **Dependency Management**
- pdf2image added to requirements.txt
- System dependencies documented

✅ **Helper Functions**
- `load_pdf_pages()` converts PDFs to images
- `save_extraction_json()` serializes extraction results
- `setup_logging()` configures dual logging

✅ **Core Pipeline**
- `process_case()` orchestrates full pipeline
- Handles PDF → images → preprocess → extract → graph → export
- Stop-on-error behavior implemented

✅ **Error Handling**
- ProcessingError exception defined
- Stage-specific error wrapping
- Clear error messages to user

✅ **CLI Integration**
- `process` command connects to pipeline
- Progress feedback during processing
- Summary statistics displayed
- Error handling with helpful messages

✅ **Testing**
- Unit tests for helpers (PDF loading)
- Integration tests for pipeline
- CLI integration tests
- Manual testing completed

✅ **Documentation**
- CLI usage guide created
- Installation instructions
- Troubleshooting section

---

## Execution Options

Plan complete and saved to `docs/plans/2026-01-22-cli-pipeline-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
