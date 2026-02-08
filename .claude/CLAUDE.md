# CLAUDE.md — Instructions for Claude Code

> **Version:** 2.10.0
> **Last Updated:** 2026-02-07
> **Status:** Master instructions file (LLM-powered OCR cleanup pipeline)

---

## Project Identity

You are building the **Civic Table** platform — **civic infrastructure for documentary recovery**. The platform enables dispossessed families, marginalized communities, and researchers to author their own evidentiary records by making degraded archives legible to power structures.

**Current Focus:** Cuban property restitution (founding case)
**Generalizable To:** Genealogy, Holocaust/WWII restitution, Indigenous land claims, investigative journalism, academic historical research

The platform implements methodology developed at the **Farmer House Democratic Repair Lab** at Huston-Tillotson University, grounded in Dr. Robert Ceresa's civic architecture framework.

**Brand Hierarchy:**
- **Civic Table LLC** — Primary brand, client-facing service, platform owner
- **Farmer House** — Methodology developer, optional institutional verifier

**See:** `docs/strategy/CIVIC_ARCHITECTURE_VISION.md` for the complete strategic framework.

---

## Critical Constraints

### 1. The Air Gap Architecture

The system has TWO ZONES that must remain separate:

**Zone A (The Factory)** — Python backend
- Internal processing only
- OCR, LLM text cleanup, AI entity/relation extraction
- Clients NEVER see this zone

**Zone B (The Vault)** — Next.js frontend
- Read-only static rendering
- Clients can ONLY view, never upload/edit/delete
- Consumes `graph_data.json` from Zone A

**See:** `docs/architecture/ARCHITECTURE.md` for complete system design.

### 2. Legal Posture (Two-Tier System)

The platform operates on a **two-tier system** for AI-generated content:

**Tier 1 — Dossier (legal-grade):**
- Forensic facts ONLY. "Document X states Y owned Z in 1958."
- No interpretation, no speculation, no conclusions.
- Extraction prompts (entity/relation) stay factual — they extract what's IN documents.
- This tier produces artifacts that could theoretically support a legal claim.

**Tier 2 — AI Analysis (research-grade):**
- Narratives, entity descriptions, document analyses.
- For families and researchers, never for court.
- MAY interpret, connect dots, speculate on likely explanations, note what's missing.
- Relevance scoring is case-relative (importance to the specific family's story).
- All output labeled TIER_3_AI — the disclaimer IS the guardrail.

**FORBIDDEN (both tiers):**
- "This proves ownership"
- "You have a strong/valid legal case"
- Anything that sounds like legal advice

**The line:** Interpretation and informed speculation = allowed in Tier 2. Legal conclusions = never.

**See:** `docs/architecture/POSTURING.md` for organizational strategy.

### 3. The Verification Tiers

Every data point MUST have a `verification` field with 4-tier system (TIER_3_AI → TIER_1_CERTIFIED).

TIER_3 AI output is interpretive by design — the tier label communicates trustworthiness, not the content tone. Analyst promotion to TIER_2 is a review/edit workflow, not a rubber stamp on conservative AI output.

**See:** `farmer_factory/structure/SCHEMA.md` for complete verification schema.

---

## Tech Stack

### Factory (Python)
- Python 3.10+, Pydantic, NetworkX
- Google Cloud Vision (OCR)
- Anthropic Claude API (extraction)
- dedupe (ML entity resolution)

### Vault (Next.js)
- Next.js 16, TypeScript, Tailwind CSS
- shadcn/ui (Radix primitives + Tailwind)
- react-force-graph-2d (visualization)
- Clerk (OAuth authentication) - planned
- Supabase (PostgreSQL with RLS) - planned

---

## Documentation Map

### For Claude Code (this directory)
- **CLAUDE.md** (this file) - Master instructions
- **ROADMAP.md** - Project roadmap and phase tracking

### Strategy & Vision (START HERE for big picture)
- **`docs/strategy/`**
  - `CIVIC_ARCHITECTURE_VISION.md` - **Core strategic document**: civic architecture framework, market analysis, competitive landscape, generalization roadmap

### Architecture & Design
- **`docs/architecture/`**
  - `ARCHITECTURE.md` - System design, Air Gap
  - `SECURITY.md` - Authentication, authorization
  - `POSTURING.md` - Organizational strategy (Farmer House relationship)
  - `FRONTEND.md` - UI design system
  - `TESTING.md` - Testing strategy
  - `DOMAIN_CONFIGURATION.md` - **Domain abstraction schema** (technical design)

### Domain Configuration
- **`farmer_factory/domains/`** - Multi-domain support infrastructure
  - `README.md` - **Complete domain system documentation**
  - `models.py` - Pydantic models for domain configs
  - `loader.py` - YAML loader with caching
  - `registry.py` - Singleton registry for active domain
  - `configs/cuban_property/` - Cuban property restitution domain
    - `domain.yaml` - Domain manifest (5 entity types, 28 relation types)
    - `prompts/system_context.txt` - LLM extraction context

**Key Integration Points:**
- `structure/schema.py` - Dynamic EntityType/RelationType from domain
- `extract/llm.py` - Domain-aware prompts and extraction hints
- `cli.py` - `--domain` flag on all commands (default: cuban_property)

### Case-Level Focus Configuration
- **`cases/{CASE-ID}/case.yaml`** - Per-case focus (optional, analyst-created)
  - `CaseFocus` model in `intake/manifest.py` — `primary_subjects`, `primary_assets`, `focus_context`
  - Loaded by `load_case_focus(case_dir)` → returns `None` if missing/malformed (graceful degradation)
  - Threaded via explicit parameter passing (not global state) through:
    - `extract/prompts/zero_shot.py` — entity + relation prompts (NOT cleanup)
    - `extract/llm.py` → `extract/pipeline.py` → `processing/pipeline.py`
    - `narrative/prompts.py` + `narrative/generator.py`
    - `narrative/entity_descriptions.py` + `narrative/document_analysis.py`
  - ~50-100 tokens per prompt, `focus_context` capped at 500 chars
  - OCR cleanup deliberately excluded — cleanup is mechanical text normalization

### Operational Guides
- **`docs/guides/`**
  - `ADMIN_GUIDE.md` - System administration
  - `ANALYST_GUIDE.md` - Verification workflow

### Module Documentation
- **`farmer_factory/intake/`**
  - `document_groups.py` - Multi-part document grouping (auto-detect + analyst review)
  - `manifest.py` - `ManifestManager` + `CaseFocus` model + `load_case_focus()` (reads `case.yaml`)

- **`farmer_factory/extract/`**
  - `README.md` - Module overview
  - `PROMPTS.md` - LLM extraction prompts
  - `chunker.py` - Document text chunking (5000-char chunks, 10% overlap)

- **`farmer_factory/narrative/`**
  - `generator.py` - Batch case narrative generation (period-based, uses Sonnet)
  - `entity_descriptions.py` - Per-entity descriptions (uses Haiku, writes `entity_descriptions.json`)
  - `document_analysis.py` - Per-document structured analysis (uses Haiku, writes `document_analyses.json`)
  - `prompts.py` - LLM prompts for narrative and summary generation
  - `models.py` - Pydantic models for CaseNarrative, NarrativePeriod, DocumentAnalysis, etc.

- **`farmer_factory/structure/`**
  - `README.md` - Graph construction & deduplication
  - `SCHEMA.md` - Complete JSON/Pydantic schema
  - `DATA_DICTIONARY.md` - Field-level reference
  - `INTEGRATION.md` - Integration guide
  - `postprocessor.py` - Graph post-processing (transitive redundancy removal, location validation)

### Test Infrastructure
- **`tests/golden/`** - Golden standard evaluation dataset
  - `data/sample_escritura.txt` - Sample notarial document
  - `data/expected_extraction.json` - Expected extraction output
  - `test_golden_evaluation.py` - Extraction quality tests

- **`farmer_factory/prepare/`**
  - `README.md` - Module overview
  - `PREPROCESSING.md` - Image processing pipeline

- **`farmer_factory/dossier/`**
  - `templates/` - LaTeX Jinja2 templates for PDF generation
  - `styles/civictable.sty` - Custom LaTeX style

### Vault (Frontend) Scroll Timeline Components
- **`farmer_vault/components/Timeline/`** - Scroll-driven timeline experience
  - `HeroSection.tsx` - 100vh hero with case name, doc count, AI disclaimer, scroll chevron
  - `ScrollTimeline.tsx` - Client container merging events + gaps with sticky spine
  - `ScrollEventNode.tsx` - 60vh+ progressive reveal (IntersectionObserver, 4 stages)
  - `ScrollGap.tsx` - 20vh amber-pulsed documentary gap indicator
  - `StickySpine.tsx` - Sticky left-edge year markers with active highlight
  - `PlaceholderSection.tsx` - Reusable "coming soon" section for geo/graph

### Vault (Frontend) Shared Modules
- **`farmer_vault/lib/document-groups.ts`** - Document group utilities (shared by all API routes)
  - `loadDocumentGroups()` - Load and validate `document_groups.yaml`
  - `buildFileToGroupMap()` - Map file stems to groups
  - `matchExtractionToGroup()` - Match extraction basenames to groups
  - `findGroupForDocId()` - Resolve `doc_` prefixed IDs to groups
  - `findGroupExtractionFiles()` - Find and sort extraction JSONs for a group
  - `inferType()` - Heuristic document type inference

**API routes using shared module:**
- `api/cases/[caseId]/documents/` - Document list (grouped aggregation)
- `api/cases/[caseId]/document/[docId]/` - Document detail (multi-page)
- `api/cases/[caseId]/document/[docId]/image/` - Image serving (`?page=N`)
- `api/cases/[caseId]/timeline/` - Timeline periods (grouped documents)
- `api/cases/[caseId]/entity/[entityId]/` - Entity detail (source document resolution, merges `entity_descriptions.json`)

**Output file layout** (`cases/{caseId}/output/`):
- `graph_data.json` - Knowledge graph (entities, relations, metadata)
- `case_narrative.json` - Period-based case narrative (Sonnet)
- `entity_descriptions.json` - Per-entity prose descriptions (Haiku) — separate file, survives graph rebuilds
- `document_analyses.json` - Per-document structured analysis (Haiku) — separate file, survives graph rebuilds

### Implementation Plans
- **`docs/plans/`** - Dated design and implementation docs
  - `2026-01-27-latex-dossier-module-design.md` - Dossier module design
  - `2026-01-27-academic-kg-improvements.md` - Chilean KG paper optimizations
  - `2026-01-27-event-entity-type-design.md` - EVENT as first-class entity (design only)

---

## Implementation Rules

### Python Code
- Use Pydantic for ALL data models
- Type hints on ALL functions
- Docstrings on public functions
- Log all processing steps
- Handle errors gracefully

### LLM Prompts
- Use prompts EXACTLY as specified in `farmer_factory/extract/PROMPTS.md`
- Parse responses into Pydantic models
- Handle malformed responses gracefully
- **Extraction prompts** (entity/relation): factual only — extract what's in documents
- **AI analysis prompts** (narrative/descriptions/document analysis): may interpret, speculate, connect dots
- Never let any LLM make legal conclusions (ownership validity, case strength)

### Frontend
- Dark theme (Slate-900 background)
- Monospace fonts for data
- Verification badges on all nodes
- TIER_3_AI disclaimer wherever unverified data appears

---

## Common Tasks

### List available domains
```bash
python -m farmer_factory.cli list-domains
```

### Create a case with domain
```bash
python -m farmer_factory.cli create-case --id CASE-ID --name "Name" --family "Family" --domain cuban_property
```

### Detect multi-part document groups
```bash
# Auto-detect groups from filename patterns (e.g., doc_1.pdf, doc_2.pdf)
python -m farmer_factory.cli detect-groups CASE-ID
# Review generated document_groups.yaml, change status DRAFT → CONFIRMED
```

### Configure case focus (optional, before processing)
Create `cases/{CASE-ID}/case.yaml` to tell LLM prompts whose story matters:
```yaml
focus:
  primary_subjects: ["Mario Ceresa", "Ceresa family"]
  primary_assets: ["Villa Aurelia"]
  focus_context: "The Ceresa family is tracing their heritage back to Cuba..."
```
Injected into entity extraction, relation extraction, narrative generation,
entity descriptions, and document analyses. NOT injected into OCR cleanup
(cleanup stays unbiased). Everything works without case.yaml — it's optional.

### Process documents
```bash
python -m farmer_factory.cli process CASE-ID --domain cuban_property --force-typed
```

### Train entity deduplication
```bash
# Interactive labeling (default)
python -m farmer_factory.cli train-deduplication CASE-ID --domain cuban_property --entity-type PERSON
python -m farmer_factory.cli train-deduplication CASE-ID --entity-type LOCATION
python -m farmer_factory.cli train-deduplication CASE-ID --entity-type PROPERTY
python -m farmer_factory.cli train-deduplication CASE-ID --entity-type ORGANIZATION

# From CONFIRMED entity groups (no interactive prompts)
python -m farmer_factory.cli train-deduplication CASE-ID --entity-type PERSON --from-groups
```

### Rebuild graph from existing extractions (no OCR/LLM cost)
```bash
# After retraining dedupe models, rebuild graph without re-running OCR or LLM
python -m farmer_factory.cli rebuild-graph CASE-ID
# Clears stale entity_groups/, regenerates DRAFT merge files, applies CONFIRMED merges
```

### Apply entity merges (after analyst reviews entity_groups/*.yaml)
```bash
python -m farmer_factory.cli apply-merges CASE-ID
python -m farmer_factory.cli apply-merges CASE-ID --include-drafts  # preview
```

### Merge two entities manually (analyst-driven)
```bash
python -m farmer_factory.cli merge-entities CASE-ID ENTITY_A ENTITY_B
```

### Clean case for re-processing
```bash
python -m farmer_factory.cli clean CASE-ID --confirm
```

### List entities in a case
```bash
python -m farmer_factory.cli list-entities CASE-ID [--type PERSON|PROPERTY|ORGANIZATION|LOCATION|DOCUMENT]
```

### Generate entity descriptions (cheap, uses Haiku)
```bash
python -m farmer_factory.cli generate-descriptions CASE-ID
# Now runs automatically at end of `process` pipeline (non-fatal on failure)
# Writes output/entity_descriptions.json — separate from graph_data.json
# Incremental: re-running skips entities that already have descriptions
# Survives rebuild-graph and apply-merges
# Standalone command still available for regeneration
```

### Generate document analyses (cheap, uses Haiku)
```bash
python -m farmer_factory.cli generate-analyses CASE-ID
# Now runs automatically at end of `process` pipeline (non-fatal on failure)
# Writes output/document_analyses.json — separate from graph_data.json
# Incremental: re-running skips documents that already have analyses
# Survives rebuild-graph and apply-merges
# Standalone command still available for regeneration
```

### Generate forensic dossier PDF
```bash
python -m farmer_factory.cli generate-dossier CASE-ID --property-id X --family-member-id Y --domain cuban_property [--dry-run]
```

**Note:** The `--domain` flag defaults to `cuban_property` if not specified.

---

## Current Phase

**See:** `.claude/ROADMAP.md` for current implementation status.

**Recent:** Phase 9G - Case-Level Focus Configuration (✅ COMPLETE - 2026-02-07)
**Status:** case.yaml focus config threaded through all LLM prompts (except cleanup)

### Completed Phases
- Phase 6 - Narrative Generation (✅ 2026-01-25)
- Phase 8A - Frontend MVP Demo (✅ 2026-01-25)
- Phase 8A.1 - Document-First Frontend (✅ 2026-01-26)
- Phase 8A.2 - LaTeX Dossier Module (✅ 2026-01-27)
- Strategic Vision Document (✅ 2026-01-27)
- Phase 9 - Domain Configuration System (✅ COMPLETE - 2026-01-27)
  - Pydantic models, YAML loader, registry singleton
  - Cuban property domain fully specified (5 entities, 28 relations)
  - **Integration complete:**
    - `extract/llm.py` - Domain-aware prompts and extraction hints
    - `structure/schema.py` - Dynamic enum generation from domain config
    - CLI - `--domain` flag on all relevant commands
    - Tests - Domain fixture in conftest.py
- Phase 9A - Academic KG Improvements (✅ COMPLETE - 2026-01-27)
  - Document text chunking (5000-char, 10% overlap) from Chilean KG paper
  - Graph post-processing for transitive redundancy removal
  - Location hierarchy validation with cycle detection
  - LocationNature/OrganizationNature enums for disambiguation
  - Golden standard evaluation dataset for extraction quality
- Phase 9A.3 - OCR Translation & Text Normalization (✅ COMPLETE - 2026-01-28)
  - Dual-backend translator: local (CTranslate2/Argos) or GCP Cloud Translation
  - OCR text normalization (hyphenation, newlines)
  - Feature-flagged (`TRANSLATION_ENABLED`, `TRANSLATION_BACKEND`)
  - Frontend "English" tab for translated documents
- Phase 9B - Document Grouping (✅ COMPLETE - 2026-01-27)
  - Auto-detect multi-part documents from filename patterns
  - Analyst review workflow (DRAFT → CONFIRMED)
  - Unified DOCUMENT entities for grouped files
  - CLI: `detect-groups` command
- Phase 9C - Entity Merge Authority (✅ COMPLETE - 2026-01-29)
  - YAML-based merge authority with DRAFT/CONFIRMED two-level status
  - Per-type entity group files in `entity_groups/`
  - Graph surgery engine (node merge, relation rewrite, metadata recompute)
  - CLI: `apply-merges`, `merge-entities`, `rebuild-graph` commands
  - Merge conflict provenance via `_merge_conflicts` dict (not list-valued fields)
  - **Dedupe merge log:** `GraphBuilder.merge_log` records all dedupe merge decisions; `_generate_merge_files()` writes real DRAFT clusters (not empty `clusters=[]`)
  - **document_id injection:** `rebuild_graph` and `process_case` inject `document_id` into processing_metadata so `_create_document_entity` doesn't produce phantom `doc_N` nodes
  - Pipeline integration + 54 tests
- Phase 9D - Frontend Document Grouping (✅ COMPLETE - 2026-01-29)
- Phase 9E - Scroll-Driven AI Analysis (✅ COMPLETE - 2026-01-30)
  - Scroll experience: 100vh hero → progressive timeline → placeholder sections
  - `ScrollEventNode` with IntersectionObserver 4-stage progressive reveal
  - CONFISCATED events: red pulse + `era-expropriation` tint
  - `StickySpine` with year markers and active highlight
  - `ScrollGap` with amber pulse for documentary gaps
  - Sidebar restructured: 4 top-level items, nested sub-items under AI Analysis
  - New routes: `/narrative/chronological`, `/narrative/geolocation`, `/narrative/graph`
  - Old `/graph` route redirects to `/narrative/graph`
  - `prefers-reduced-motion`: all content visible immediately, no animations
  - Removed stale `lib/graph-api.ts`
  - All Vault API routes support `document_groups.yaml` (documents list, single doc, image, timeline, entity detail)
  - **Shared `lib/document-groups.ts` utility** — single source of truth for YAML loading, file-to-group mapping, extraction matching, group-by-ID lookup, and type inference. Used by all 5 API routes.
  - Multi-page document viewer with page navigation (prev/next)
  - Grouped documents aggregated as single entries in document list
  - Entity source documents resolve to group names (not raw extraction stems)
  - `js-yaml` dependency for YAML parsing in API routes
  - Expanded `inferType()` heuristics (Property, Survey, Financial, Inheritance)
  - Date sort order toggle (ascending/descending)
  - Iframe-based PDF viewer replacing manual zoom controls
- Phase 9F - LLM OCR Cleanup (✅ COMPLETE - 2026-02-07)
  - LLM-powered OCR text cleanup step inserted before entity extraction (Haiku, ~$0.0016/doc)
  - Fixes broken words, removes artifacts, restores paragraph structure
  - Preserves original language — no translation, no paraphrasing
  - Graceful degradation: falls back to raw OCR on failure
  - Full pipeline flow: OCR → Cleanup (LLM) → Translation (GCP, on by default) → Entity Extraction* → Relation Extraction* → Graph Build → Case Narrative* → Entity Descriptions* → Document Analyses* (*=case focus injected if case.yaml exists)
  - Output saved to `ocr_cleaned/` directory + embedded in extraction JSON (`ocr_result.cleaned_text`)
  - API serves cleaned text by default, includes `rawOcrText` when available
  - Frontend toggle: "Show Raw OCR" / "Show Cleaned" on OCR tab
  - Prompt: `farmer_factory/extract/prompts/zero_shot.py` → `build_cleanup_prompt()`
  - Method: `LLMExtractionService.clean_ocr_text()` in `extract/llm.py`
- Phase 9G - Case-Level Focus Configuration (✅ COMPLETE - 2026-02-07)
  - `case.yaml` in each case directory with `focus:` block (primary_subjects, primary_assets, focus_context)
  - `CaseFocus` Pydantic model in `intake/manifest.py` with validation (list cleaning, 1500-char truncation)
  - `load_case_focus(case_dir)` — fail-soft loader, returns None if missing/malformed
  - Threaded via explicit parameter passing through entity extraction, relation extraction, narrative generation, entity descriptions, and document analyses
  - OCR cleanup deliberately excluded — cleanup is mechanical text normalization
  - Graceful degradation: everything works without case.yaml
  - TEST-CERESA case.yaml created (Mario Ceresa / Ceresa family / Villa Aurelia)
  - Two-tier prompt posture: extraction stays factual; AI analysis (narratives, descriptions, document analyses) allows interpretation
  - 29 tests in `tests/intake/test_case_focus.py`

### Strategic Priorities (from Civic Architecture Vision)
1. **Domain Configuration Abstraction** — ✅ Complete
2. **Methodology Publication** — Document at general level (not Cuba-specific)
3. **Identify Domain #2 Partner** — Genealogy, academic archive, or parallel restitution

### Technical Roadmap (Next Steps)
- Phase 8A.3 - Property Geolocation Module (future enhancement)
- Phase 8B - Authentication & Database Integration
- Domain #2 implementation (post-partner identification)

---

## What NOT to Do

1. **Never** make legal conclusions (ownership validity, case strength) in any prompt or output
2. **Never** restrict AI analysis prompts to "only what documents state" — interpretation is allowed (see Two-Tier System)
3. **Never** allow Zone B to modify data
4. **Never** display TIER_3_AI data without disclaimer
5. **Never** skip the verification field on any node/link
6. **Never** expose raw AI inference to clients without context
6. **Never** run tests that call the Anthropic API (`tests/extract/test_integration.py`, `tests/golden/`) without asking first — these use streaming API calls and burn through credits quickly. Safe to run: all other test files (they use mock extraction)

---

*For detailed documentation, see the files referenced above. This is your navigation guide to the codebase.*

<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

*No recent activity*
</claude-mem-context>