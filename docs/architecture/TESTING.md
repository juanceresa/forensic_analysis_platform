# Farmer House Forensic Intelligence Platform — Testing Specification

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.0.0
> **Last Updated:** 2026-01-21
> **Status:** MVP1 Testing Protocol

---

## Overview

This document defines the testing strategy for MVP1, including the golden dataset, acceptance criteria, and regression testing approach.

**Testing Philosophy:**
- Validate early, validate often
- Test each pipeline stage independently before integration
- Maintain golden dataset for regression testing
- Focus on forensic fact accuracy, not perfection

---

## Golden Dataset

### Specification

**Size:** 20 manually annotated documents

**Selection Criteria:**
- Representative of Ceresa Archive diversity
- Mix of document types (deeds, certificates, correspondence, decrees)
- Range of OCR difficulties (typed clean → handwritten degraded)
- Known entities and relations (manually verified)

### Composition

| Document Type | Count | OCR Quality | Purpose |
|---------------|-------|-------------|---------|
| Typed deed (clean) | 3 | Excellent | Baseline for high-quality extraction |
| Typed deed (faded) | 3 | Good | Test enhancement pipeline |
| Handwritten certificate | 4 | Partial | Test vision model path |
| Mixed (typed + handwritten) | 3 | Partial | Test region segmentation |
| Confiscation decree | 2 | Good | Test legal entity extraction |
| Correspondence | 2 | Variable | Test informal language handling |
| Property registry | 2 | Excellent | Test structured data extraction |
| Photograph/map | 1 | N/A | Negative test case (should skip OCR) |

### Annotation Format

Each golden dataset document has a JSON annotation file:

```json
{
  "document_id": "GOLDEN-001",
  "source_file": "golden_dataset/deed_1958_typed.pdf",
  "annotator": "Human analyst",
  "annotation_date": "2025-01-21",
  "ground_truth": {
    "entities": [
      {
        "type": "PERSON",
        "value": "Mario Ceresa",
        "context": "comparece Don Mario Ceresa, propietario",
        "confidence_expectation": 0.90
      },
      {
        "type": "PROPERTY",
        "value": "Central Santa Maria",
        "context": "Central Santa Maria ubicado en Florida, Camagüey",
        "confidence_expectation": 0.85
      }
    ],
    "relations": [
      {
        "type": "OWNS",
        "source": "Mario Ceresa",
        "target": "Central Santa Maria",
        "temporal": {
          "start_date": "1945-01-01",
          "precision": "year"
        }
      }
    ],
    "temporal_facts": [
      {
        "event": "Document signed",
        "date": "1958-03-15",
        "precision": "exact"
      }
    ]
  },
  "expected_challenges": [
    "None - baseline quality document"
  ],
  "manual_transcription": "..."
}
```

### Storage

```
golden_dataset/
├── documents/
│   ├── GOLDEN-001.pdf
│   ├── GOLDEN-002.pdf
│   └── ...
├── annotations/
│   ├── GOLDEN-001.json
│   ├── GOLDEN-002.json
│   └── ...
├── preprocessing_expected/
│   └── GOLDEN-001/
│       ├── deskew_angle.txt     # Expected: 0.0±0.5
│       ├── ocr_quality.txt      # Expected: "excellent"
│       └── triage_path.txt      # Expected: "TYPED"
└── README.md
```

---

## Unit Testing

### Preprocessing Tests

```python
# tests/test_preprocessing.py

import pytest
from pathlib import Path
from prepare.pipeline import PreprocessingPipeline
from prepare.triage import triage_document

class TestPreprocessing:
    @pytest.fixture
    def pipeline(self):
        return PreprocessingPipeline()

    def test_triage_typed_document(self):
        """Triage should correctly identify typed documents."""
        image = load_test_image("golden_dataset/GOLDEN-001.pdf")
        result = triage_document(image)

        assert result.path == DocumentPath.TYPED
        assert result.confidence > 0.80
        assert result.estimated_ocr_quality in ["excellent", "good"]

    def test_triage_handwritten_document(self):
        """Triage should route handwritten docs to vision model."""
        image = load_test_image("golden_dataset/GOLDEN-005.pdf")
        result = triage_document(image)

        assert result.path == DocumentPath.HANDWRITTEN
        assert result.confidence > 0.70

    def test_deskew_accuracy(self):
        """Deskew should correct rotation within 0.5 degrees."""
        image = load_rotated_test_image(rotation=5.0)
        corrected, angle = deskew_image(image)

        assert abs(angle - 5.0) < 0.5

    def test_binarization_preserves_text(self):
        """Binarization should not lose text."""
        image = load_test_image("golden_dataset/GOLDEN-003.pdf")
        binary = binarize_image(image, method="sauvola")

        # Text regions should be preserved
        text_density_before = estimate_text_density(image)
        text_density_after = estimate_text_density(binary)

        assert text_density_after >= text_density_before * 0.95
```

### Entity Extraction Tests

```python
# tests/test_extraction.py

class TestEntityExtraction:
    @pytest.fixture
    def extractor(self):
        return EntityExtractor(model="claude-3-haiku")

    def test_entity_precision_on_golden_set(self, extractor):
        """Entity extraction meets precision target."""
        results = []

        for doc in load_golden_dataset():
            extracted = extractor.extract(doc.ocr_text)
            ground_truth = doc.ground_truth.entities

            precision = calculate_precision(extracted, ground_truth)
            recall = calculate_recall(extracted, ground_truth)

            results.append({"precision": precision, "recall": recall})

        avg_precision = sum(r["precision"] for r in results) / len(results)
        avg_recall = sum(r["recall"] for r in results) / len(results)

        assert avg_precision >= 0.75, f"Precision {avg_precision:.2f} below target 0.75"
        assert avg_recall >= 0.65, f"Recall {avg_recall:.2f} below target 0.65"

    def test_no_hallucinated_entities(self, extractor):
        """Extracted entities must appear in source text."""
        doc = load_golden_dataset()[0]
        extracted = extractor.extract(doc.ocr_text)

        for entity in extracted:
            # Entity value or close variant must appear in OCR text
            assert entity_appears_in_text(entity.value, doc.ocr_text), \
                f"Entity '{entity.value}' not found in source text"
```

### Graph Construction Tests

```python
# tests/test_graph.py

class TestGraphConstruction:
    def test_no_orphan_nodes_below_threshold(self):
        """Orphan nodes should be <10% of total."""
        graph = build_test_graph()
        orphan_count = count_orphan_nodes(graph)
        orphan_pct = orphan_count / len(graph.nodes)

        assert orphan_pct < 0.10, f"Orphan nodes {orphan_pct:.1%} exceeds 10%"

    def test_temporal_conflict_resolution(self):
        """Conflicts should resolve per SCHEMA.md rules."""
        # Test case: Two docs say different dates
        entities = [
            create_test_entity("Mario Ceresa", date="1958-03-15", tier="TIER_2_ANALYST"),
            create_test_entity("Mario Ceresa", date="1958-06-20", tier="TIER_3_AI")
        ]

        resolved = resolve_temporal_conflict(entities)

        # Should choose TIER_2_ANALYST date (analyst-verified takes precedence)
        assert resolved.date == "1958-03-15"
        assert resolved.has_conflict == True
        assert len(resolved.alternative_dates) == 1

    def test_coreference_merges_obvious_duplicates(self):
        """'Mario Ceresa' and 'Don Mario Ceresa' should merge."""
        entities = [
            {"name": "Mario Ceresa", "source": "DOC-001"},
            {"name": "Don Mario Ceresa", "source": "DOC-002"}
        ]

        clusters = perform_coreference(entities)

        assert len(clusters) == 1
        assert clusters[0].canonical_form == "Mario Ceresa"
        assert len(clusters[0].variants) == 2

    def test_coreference_keeps_ambiguous_separate(self):
        """Common names without context should not merge."""
        entities = [
            {"name": "José Fernández", "source": "DOC-001", "context": "notary"},
            {"name": "José Fernández", "source": "DOC-050", "context": "witness"}
        ]

        clusters = perform_coreference(entities)

        # Should create separate clusters or flag as ambiguous
        assert len(clusters) >= 1
        if len(clusters) == 1:
            assert clusters[0].ambiguous == True
```

---

## Integration Testing

### End-to-End Test

```python
# tests/test_integration.py

class TestEndToEnd:
    def test_single_document_pipeline(self):
        """Process one document from PDF to graph_data.json."""
        # Input
        pdf_path = Path("golden_dataset/GOLDEN-001.pdf")
        output_dir = Path("test_output/GOLDEN-001")

        # Run full pipeline
        result = process_document_pipeline(pdf_path, output_dir)

        # Validate output
        assert result.success == True
        assert (output_dir / "graph_data.json").exists()

        graph_data = load_json(output_dir / "graph_data.json")

        # Validate structure
        assert validate_graph_schema(graph_data)

        # Validate content against golden dataset
        ground_truth = load_ground_truth("GOLDEN-001")
        precision = compare_to_ground_truth(graph_data, ground_truth)

        assert precision >= 0.75

    def test_batch_processing(self):
        """Process 10-doc batch without failures."""
        pdf_paths = list(Path("golden_dataset/documents").glob("GOLDEN-00[1-9].pdf"))[:10]
        results = batch_process(pdf_paths, output_dir=Path("test_output/batch"))

        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results)

        assert success_rate >= 0.90, f"Success rate {success_rate:.1%} below 90%"

        # Check audit trail completeness
        for result in results:
            assert result.audit_log_exists
            assert result.processing_complete
```

---

## Regression Testing

### Automated Regression Suite

Run before any prompt changes or major refactoring:

```bash
# Run full regression suite
pytest tests/ --golden-dataset --cov=farmer_factory --cov-report=html

# Quick regression (critical tests only)
pytest tests/ -m "regression" --maxfail=1
```

### Regression Test Markers

```python
@pytest.mark.regression
def test_critical_entity_extraction():
    """Must pass before any deployment."""
    ...

@pytest.mark.slow
def test_full_batch_300_docs():
    """Runs on golden dataset + full archive."""
    ...

@pytest.mark.prompt_change
def test_prompt_version_consistency():
    """Ensures prompt changes don't break existing extractions."""
    ...
```

### Prompt Change Protocol

When modifying prompts in `config/prompts/`:

1. **Backup:** Copy current prompt to `prompts/archive/v{version}/`
2. **Version:** Increment version in `PROMPT_VERSIONS`
3. **Test:** Run regression suite on golden dataset
4. **Compare:** Compare new outputs to previous version
5. **Document:** Record changes in `prompts/CHANGELOG.md`

If regression tests fail:
- Precision/recall drops >5%: **Reject** change
- Precision/recall drops 2-5%: **Review** manually
- Precision/recall improves: **Accept**, document improvement

---

## Quality Metrics Dashboard

Generate after each test run:

```
Quality Metrics Report
======================
Test Run: 2025-01-21 14:30:00
Golden Dataset: 20 documents

Preprocessing:
  Triage accuracy:     85% (17/20 correct path)
  Avg processing time: 2.3 min/doc
  Failures:            0

Entity Extraction:
  Precision:           78% (above target 75%)
  Recall:              68% (above target 65%)
  F1 Score:            0.73
  Hallucinations:      2% (4/200 entities)

Relation Extraction:
  Precision:           72% (above target 70%)
  Recall:              63% (above target 60%)
  F1 Score:            0.67

Coreference Resolution:
  F1 Score:            74% (above target 70%)
  Auto-merge rate:     65%
  Review queue:        25%
  Incorrect merges:    8% (acceptable for MVP1)

Graph Construction:
  Orphan nodes:        7% (below 10% threshold)
  Avg node degree:     5.2
  Temporal conflicts:  12% (resolved per rules)

Overall: PASS ✓
Blocker issues: 0
Warnings: 3 (see details below)
```

---

## Manual QA Protocol

Before releasing to client:

### Checklist

- [ ] **No legal conclusions** — Manual review of 20 random summaries
- [ ] **Verification tiers** — All nodes have valid tier + confidence
- [ ] **Legal disclaimer** — Prominent on all frontend pages
- [ ] **Audit trail** — Complete for all processed documents
- [ ] **Source attribution** — Every fact traces to source document
- [ ] **Temporal consistency** — No impossible dates (e.g., person dies before birth)
- [ ] **No hallucinations** — Sample check: entities appear in source docs
- [ ] **Frontend functional** — Graph renders, filters work, dossier panel functional

### QA Sign-Off

```
QA Reviewer: _______________
Date: _______________
MVP1 Release: [ ] APPROVED  [ ] REJECTED
Notes: _______________
```

---

## Continuous Testing (MVP2+)

Future enhancements:

- CI/CD integration (GitHub Actions)
- Automated quality monitoring
- Drift detection (prompt/model changes)
- Production error tracking
- A/B testing for prompt improvements

---

*Testing is not about achieving perfection—it's about knowing what works, what doesn't, and being honest about both.*
