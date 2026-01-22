# Structure Module Integration

Complete end-to-end integration with prepare and extract modules.

## Full Pipeline Example

```python
from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import ExtractionPipeline, OCRService, VisionExtractionService, LLMExtractionService, SchemaValidator
from farmer_factory.structure import KnowledgeGraph, EntityResolver, GraphBuilder, GraphExporter
from pathlib import Path
import cv2

# Initialize pipelines
prep_pipeline = PreprocessingPipeline()
extract_pipeline = ExtractionPipeline(
    ocr_service=OCRService(),
    vision_service=VisionExtractionService(),
    llm_service=LLMExtractionService(),
    validator=SchemaValidator()
)

# Initialize graph builder
graph = KnowledgeGraph(case_id="case_001")
resolver = EntityResolver(similarity_threshold=0.85)
builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

# Process multiple documents
for doc_path in Path("documents/").glob("*.png"):
    # Preprocess
    raw_image = cv2.imread(str(doc_path), cv2.IMREAD_GRAYSCALE)
    preprocessed = prep_pipeline.process_page(raw_image)

    # Extract entities
    extraction = extract_pipeline.extract_page(preprocessed, document_id=doc_path.stem)

    # Build graph (with automatic deduplication)
    builder.add_extraction(extraction)

# Export graph
exporter = GraphExporter(knowledge_graph=graph)
exporter.save(Path("output/graph_data.json"), factory_version="1.0.0")

print(f"Processed {builder.processing_stats['documents_processed']} documents")
print(f"Extracted {builder.processing_stats['entities_extracted']} entities")
print(f"Merged {builder.processing_stats['entities_merged']} duplicates")
print(f"Added {builder.processing_stats['relations_added']} relations")
```

## Key Features

**Entity Deduplication:**
- Fuzzy name matching (configurable threshold, default 0.85)
- Automatic merge when similarity detected
- Conflict resolution with provenance tracking

**Date Normalization:**
- Flexible input: "1920", "March 1958", "1958-03-15"
- Sortable output: ISO 8601 format
- Computed fields: `*_sortable`, `*_earliest`

**Metadata Tracking:**
- Verification distribution
- Date range (earliest/latest)
- Entity/relation counts
- Processing statistics

## Tests

All 55 tests passing:
- EntityResolver: 12 tests (fuzzy matching, merging, conflicts)
- GraphBuilder: 5 tests (initialization, extraction, batch)
- GraphExporter: 9 tests (date normalization, JSON export, file save)
- Existing: 29 tests (schema, graph operations)
