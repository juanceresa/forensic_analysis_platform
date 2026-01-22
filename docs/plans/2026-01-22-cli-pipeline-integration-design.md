# CLI Pipeline Integration Design

**Goal:** Implement the `process` command to connect prepare → extract → structure modules into a complete end-to-end pipeline.

**User Story:** User drops PDFs into a case intake folder, runs `python cli.py process CASE-ID`, and gets a complete knowledge graph JSON ready for the frontend.

---

## Architecture

### Command Flow
```bash
python cli.py process CASE-CERESA
```

### Pipeline Stages
1. **PDF Loading** - Convert PDFs to images (one image per page) using pdf2image
2. **Preprocessing** - Prepare module (deskew, denoise, triage TYPED vs HANDWRITTEN)
3. **Extraction** - Extract module (OCR/Vision → entities/relations, all TIER_3_AI)
4. **Graph Building** - Structure module (entity deduplication, conflict resolution, graph construction)
5. **Export** - Save graph_data.json in force-graph format

### Directory Structure
```
cases/
  CASE-CERESA/              # User-defined case name
    intake/                 # User drops PDFs here
      1960_Mario_Ceresa.pdf
      1916_Property_Transfer.pdf
    preprocessed/           # Saved by prepare module
      1960_Mario_Ceresa_page_0.png
      1960_Mario_Ceresa_page_1.png
    extractions/            # Saved by extract module (JSON)
      1960_Mario_Ceresa_page_0.json
      1960_Mario_Ceresa_page_1.json
    output/                 # Final graph
      graph_data.json
    metadata.json           # Case info (id, name, family, created_at)
    processing.log          # Detailed processing logs
```

### Error Handling Strategy
- **Stop on first failure** (MVP approach)
- Process documents sequentially
- If any document/page fails at any stage, stop immediately
- Log error details to `processing.log` with full stack trace
- Show clear error message indicating which document/page failed
- User can fix issue and retry

---

## PDF to Image Conversion

### Library Choice
**pdf2image** (wraps poppler)
- Widely used, reliable
- Handles multi-page PDFs
- Configurable DPI

### System Requirements
- macOS: `brew install poppler`
- Ubuntu: `apt-get install poppler-utils`
- Windows: Download poppler binaries

### Implementation
```python
from pdf2image import convert_from_path

def load_pdf_pages(pdf_path: Path, output_dir: Path) -> List[Path]:
    """
    Convert PDF to images, one per page.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images

    Returns:
        List of paths to saved page images
    """
    images = convert_from_path(
        pdf_path,
        dpi=300,              # High quality for OCR
        grayscale=True,       # Matches prepare module expectations
        fmt='png'
    )

    page_paths = []
    for i, image in enumerate(images):
        page_path = output_dir / f"{pdf_path.stem}_page_{i}.png"
        image.save(page_path, 'PNG')
        page_paths.append(page_path)

    return page_paths
```

### Document ID Strategy
- PDF filename: `1960_Mario_Ceresa.pdf`
- Page IDs: `1960_Mario_Ceresa_page_0`, `1960_Mario_Ceresa_page_1`
- Keeps relationship clear for provenance tracking in graph

---

## Main Processing Loop

### High-Level Flow
```python
def process_case(case_id: str):
    """Process all PDFs in case through complete pipeline."""

    # 1. Setup paths and logging
    case_dir = Path('cases') / case_id
    intake_dir = case_dir / 'intake'
    preprocessed_dir = case_dir / 'preprocessed'
    extractions_dir = case_dir / 'extractions'
    output_dir = case_dir / 'output'

    setup_logging(case_dir / 'processing.log')

    # 2. Initialize pipelines once (reuse across all documents)
    prep_pipeline = PreprocessingPipeline()
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    # 3. Initialize graph builder
    graph = KnowledgeGraph(case_id=case_id)
    resolver = EntityResolver(similarity_threshold=0.85)
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # 4. Process each PDF
    pdfs = sorted(intake_dir.glob('*.pdf'))
    for pdf_idx, pdf_path in enumerate(pdfs, 1):
        click.echo(f"\n[{pdf_idx}/{len(pdfs)}] Processing {pdf_path.name}...")

        # Convert PDF to images
        page_images = load_pdf_pages(pdf_path, preprocessed_dir)
        click.echo(f"  Loaded {len(page_images)} pages")

        # Process each page
        for page_idx, page_path in enumerate(page_images, 1):
            click.echo(f"  Page {page_idx}/{len(page_images)}...", nl=False)

            # Preprocess
            raw_image = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
            preprocessed = prep_pipeline.process_page(raw_image)

            # Save preprocessed image
            preprocessed_path = preprocessed_dir / f"{page_path.stem}_processed.png"
            cv2.imwrite(str(preprocessed_path), preprocessed.image)

            # Extract entities
            document_id = page_path.stem
            extraction = extract_pipeline.extract_page(preprocessed, document_id=document_id)

            # Save extraction JSON
            extraction_path = extractions_dir / f"{document_id}.json"
            save_extraction_json(extraction, extraction_path)

            # Add to graph (with auto-deduplication)
            builder.add_extraction(extraction)

            click.echo(" ✓")

    # 5. Export graph
    click.echo("\nExporting graph...")
    exporter = GraphExporter(knowledge_graph=graph)
    exporter.save(output_dir / 'graph_data.json', factory_version="1.0.0")

    # 6. Print summary statistics
    click.echo("\n" + "="*60)
    click.echo("Processing Complete!")
    click.echo("="*60)
    stats = builder.processing_stats
    click.echo(f"Documents processed: {stats['documents_processed']}")
    click.echo(f"Entities extracted:  {stats['entities_extracted']}")
    click.echo(f"Entities merged:     {stats['entities_merged']}")
    click.echo(f"Relations added:     {stats['relations_added']}")
    click.echo(f"\nGraph saved to: {output_dir / 'graph_data.json'}")
```

### Progress Feedback
- Document counter: `[1/15] Processing doc.pdf...`
- Page counter: `Page 1/3... ✓`
- Stage indicators: `Preprocessing... ✓ Extracting... ✓ Building graph... ✓`
- Final summary with statistics

---

## Error Handling & Logging

### Error Handling
```python
class ProcessingError(Exception):
    """Custom exception for pipeline processing errors."""
    pass

def process_case_with_error_handling(case_id: str):
    """Wrapper with comprehensive error handling."""
    case_dir = Path('cases') / case_id

    try:
        process_case(case_id)

    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"\n❌ Processing failed: {e}", err=True)
        click.echo(f"Check detailed logs: {case_dir}/processing.log")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        click.echo(f"Check detailed logs: {case_dir}/processing.log")
        sys.exit(1)
```

### Stage-Specific Error Wrapping
```python
# PDF loading
try:
    page_images = load_pdf_pages(pdf_path, preprocessed_dir)
except Exception as e:
    raise ProcessingError(f"Failed to load PDF {pdf_path.name}: {e}")

# Preprocessing
try:
    preprocessed = prep_pipeline.process_page(raw_image)
except Exception as e:
    raise ProcessingError(f"Failed preprocessing {page_path.name}: {e}")

# Extraction
try:
    extraction = extract_pipeline.extract_page(preprocessed, document_id)
except Exception as e:
    raise ProcessingError(f"Failed extraction {document_id}: {e}")

# Graph building (should not fail with current implementation)
try:
    builder.add_extraction(extraction)
except Exception as e:
    raise ProcessingError(f"Failed adding to graph {document_id}: {e}")
```

### Logging Configuration
```python
def setup_logging(log_file: Path):
    """Configure dual logging: file (DEBUG) + console (INFO)."""

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

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

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
```

### Log Contents
- Timestamp for each document/page processed
- Processing time per stage (useful for optimization)
- Warnings: low confidence OCR, validation issues, merge conflicts
- Errors: full stack traces with context
- Summary statistics at completion

---

## Helper Functions

### Extraction JSON Serialization
```python
def save_extraction_json(extraction: ExtractionResult, output_path: Path):
    """Save extraction result to JSON with proper serialization."""
    data = {
        'entities': [e.model_dump() for e in extraction.entities],
        'relations': [r.model_dump() for r in extraction.relations],
        'confidence_scores': extraction.confidence_scores,
        'path': extraction.path.value,
        'processing_metadata': extraction.processing_metadata
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
```

### Image Loading
```python
import cv2

def load_image(image_path: Path) -> np.ndarray:
    """Load image as grayscale numpy array."""
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")
    return image
```

---

## Dependencies

### New Python Package
```python
# requirements.txt addition
pdf2image>=1.16.0    # PDF to image conversion
```

### System Dependencies
**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
apt-get install poppler-utils
```

**Windows:**
- Download poppler binaries from: https://github.com/oschwartz10612/poppler-windows/releases
- Add to PATH

---

## Testing Strategy

### Unit Test for PDF Loading
```python
# tests/test_cli_pdf_loading.py
def test_load_pdf_pages(tmp_path, sample_pdf):
    """Test PDF to image conversion."""
    output_dir = tmp_path / 'preprocessed'
    output_dir.mkdir()

    page_paths = load_pdf_pages(sample_pdf, output_dir)

    assert len(page_paths) > 0
    for path in page_paths:
        assert path.exists()
        assert path.suffix == '.png'
```

### Integration Test for Full Pipeline
```python
# tests/test_cli_integration.py
def test_process_command_end_to_end(tmp_path):
    """Test full pipeline with sample PDF."""
    # Setup test case
    case_dir = tmp_path / 'cases' / 'TEST-001'
    intake_dir = case_dir / 'intake'
    intake_dir.mkdir(parents=True)

    # Copy sample PDF
    sample_pdf = Path('farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf')
    shutil.copy(sample_pdf, intake_dir)

    # Create metadata
    metadata = {
        'id': 'TEST-001',
        'name': 'Test Case',
        'family': 'Test',
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Run CLI command
    runner = CliRunner()
    result = runner.invoke(cli, ['process', 'TEST-001'])

    # Verify success
    assert result.exit_code == 0

    # Verify outputs exist
    assert (case_dir / 'output' / 'graph_data.json').exists()
    assert (case_dir / 'processing.log').exists()

    # Verify graph structure
    with open(case_dir / 'output' / 'graph_data.json') as f:
        graph = json.load(f)

    assert 'nodes' in graph
    assert 'links' in graph
    assert 'metadata' in graph
    assert graph['metadata']['case_id'] == 'TEST-001'
    assert len(graph['nodes']) > 0  # At least some entities extracted
```

### Manual Testing Procedure
```bash
# 1. Install system dependencies
brew install poppler  # macOS

# 2. Install Python dependencies
pip install pdf2image

# 3. Create test case
python cli.py create-case --id TEST-CERESA --name "Ceresa Test" --family "Ceresa"

# 4. Copy sample PDFs
cp farmer_factory/sample_docs/*.pdf cases/TEST-CERESA/intake/

# 5. Run processing with verbose output
python cli.py process TEST-CERESA --verbose

# 6. Verify outputs
ls -la cases/TEST-CERESA/preprocessed/  # Should have PNGs
ls -la cases/TEST-CERESA/extractions/   # Should have JSONs
ls -la cases/TEST-CERESA/output/        # Should have graph_data.json

# 7. Inspect graph
cat cases/TEST-CERESA/output/graph_data.json | jq '.metadata'
cat cases/TEST-CERESA/output/graph_data.json | jq '.nodes | length'

# 8. Check logs
tail -50 cases/TEST-CERESA/processing.log
```

---

## Implementation Checklist

- [ ] Add pdf2image to requirements.txt
- [ ] Create `load_pdf_pages()` helper function
- [ ] Create `save_extraction_json()` helper function
- [ ] Create `setup_logging()` function
- [ ] Implement main `process_case()` function
- [ ] Update CLI `process` command to call `process_case()`
- [ ] Add ProcessingError exception class
- [ ] Add error handling wrapper
- [ ] Create integration test
- [ ] Test with sample PDFs
- [ ] Document system dependency installation
- [ ] Update README with usage instructions

---

## Success Criteria

✅ User can run `python cli.py process CASE-ID` and get complete graph
✅ All intermediate files saved (preprocessed images, extraction JSONs)
✅ Clear progress feedback during processing
✅ Detailed logs saved to processing.log
✅ Meaningful error messages on failure
✅ Processing statistics shown at completion
✅ Graph ready for frontend consumption (force-graph format)
