# System Architecture

## Overview

Civic Table is a two-zone forensic document analysis stack:

- `farmer_factory/`: Python processing pipeline (ingestion, OCR, extraction, graph build)
- `farmer_vault/`: Next.js read-only interface for reviewing case outputs

The default operating model is local and air-gapped: process in Factory, then inspect in Vault.

## High-Level Flow

```text
PDF Intake -> Preprocess -> OCR -> LLM Extraction -> Graph Build -> JSON Outputs -> Vault API/UI
```

Primary artifacts written under `cases/<CASE_ID>/`:

- `extractions/*.json`: per-page extraction payloads
- `ocr/*.txt`: raw OCR text
- `ocr_cleaned/*.txt`: cleaned OCR text
- `ocr_translated/*.txt`: optional translations
- `output/graph_data.json`: graph export for Vault
- `output/entity_descriptions.json`: per-entity narrative descriptions
- `output/document_analyses.json`: per-document structured analyses
- `output/case_narrative.json`: period-based case narrative
- `entity_groups/*.yaml`: analyst merge authority files
- `document_groups.yaml`: optional multi-part document grouping config
- `case.yaml`: optional per-case focus context

## Factory Pipeline

Implemented via `farmer_factory.processing.process_case`.

1. Intake loading
- Reads PDFs from `cases/<CASE_ID>/intake/`.
- Optionally processes a single file via `--file`.

2. Image preprocessing
- Runs deskew/denoise pipeline before OCR.
- Supports triage and `--force-typed` override.

3. OCR and extraction
- OCR service produces text + confidence metadata.
- LLM cleanup normalizes OCR text.
- Entity extraction and relation extraction run per page.
- Optional per-case focus (`case.yaml`) is injected into analysis-oriented prompts.

4. Graph construction
- Entities and relations are added to a `KnowledgeGraph`.
- Dedupe resolver merges likely duplicates.
- Export written to `output/graph_data.json`.

5. Merge authority generation
- Writes draft merge files under `entity_groups/`.
- Applies previously confirmed merges (if present).

6. Validation and manifest
- Validates graph export unless `--skip-validation`.
- Writes `manifest.json` for processing traceability.

## Rebuild Path

`rebuild-graph` reconstructs `graph_data.json` from saved `extractions/*.json` without re-running OCR/LLM extraction.

Use cases:

- after dedupe model retraining
- after merge review updates
- low-cost iteration on graph quality

## Analysis Path

Analysis generation is intentionally separate from raw extraction:

- `generate-descriptions`: builds `entity_descriptions.json`
- `generate-analyses`: builds `document_analyses.json`
- `generate-narrative`: builds `case_narrative.json`
- `analyze`: runs all three with a shared budget split

This supports a clean workflow: process -> review/merge -> generate interpretive outputs.

## Deployment Modes

Current repo defaults to local file-backed operation.

- Factory reads/writes `cases/` on local disk.
- Vault APIs read `../cases/<CASE_ID>/output/*.json` and related artifacts.
- Supabase upload and broader hosted architecture are present as extension paths, not the default runtime mode.

## Design Constraints

- Provenance first: extracted facts stay linked to source document IDs.
- Analyst-in-the-loop: merge and verification workflows are explicit.
- Non-destructive outputs: source intake files are preserved.
- Separation of concerns: extraction artifacts and interpretive outputs are stored independently.
