# Farmer House Forensic Intelligence Platform — Implementation Roadmap

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.9.0
> **Last Updated:** 2026-01-28
> **Status:** MVP1 Planning (with dependencies and acceptance criteria)

---

## Overview

This document provides the implementation roadmap for MVP1. It breaks down work into phases and tasks suitable for Claude Code execution.

**Strategic Vision:** See `docs/strategy/CIVIC_ARCHITECTURE_VISION.md` for the foundational strategic document that frames Civic Table as civic infrastructure for documentary recovery—generalizable beyond Cuban property restitution to genealogy, academic research, investigative journalism, and parallel restitution contexts.

---

## Strategic Priorities (from Civic Architecture Vision)

These priorities guide post-MVP development:

1. **Domain Configuration Abstraction (Phase 9)** — Pull Cuban-specific elements into config layer
2. **Methodology Publication** — Document at general level (not Cuba-specific)
3. **Identify Domain #2 Partner** — Genealogy, academic archive, or parallel restitution

**Key Insight:** 70% of the platform is domain-agnostic. The technical core (OCR → extraction → graph → verification → dossier) generalizes; only entity types, relation types, prompts, and success criteria are domain-specific.

---

## MVP1 Scope

### In Scope
- PDF intake (300 documents)
- Full preprocessing pipeline with triage
- OCR via Google Cloud Vision
- Vision model fallback for handwritten docs
- Entity/relation extraction via Claude API
- NetworkX graph construction
- JSON export
- Next.js frontend with filtered/tabbed views
- CLI interface
- **Authentication & Authorization** (Clerk OAuth 2.0 with MFA)
- **Database with RLS** (Supabase with case isolation)
- **Vercel deployment** (HTTPS, security headers)
- **Audit logging** (All access tracked)
- **Analyst verification workflow** (TIER_3_AI → TIER_2_ANALYST promotion)
- **Factory → Vault integration** (Supabase Storage for graph data)

### Out of Scope (MVP2+)
- **Gap detection for families** (deferred to analyst workflow - see ADR 2026-01-23)
- **Vision API for handwritten documents** (currently using OCR + LLM for all docs with `--force-typed`)
  - Implement real Claude Vision API extraction (send images directly to Vision API)
  - Tune triage classifier to route handwritten vs typed correctly
  - Compare quality: Vision API vs OCR+LLM for handwritten docs
  - Use Vision API only for documents where OCR struggles (<60% confidence)
- TIER_2_INSTITUTIONAL verification (Farmer House partnership not active yet)
- TIER_1_CERTIFIED promotion (external legal process)
- Multi-case support (single family for MVP1)
- Case management web UI (CLI-based for MVP1)
- Client intake portal (use external tools: Typeform, Google Drive)
- Case tracking dashboard (use Notion/Airtable for MVP1)

### Architectural Decisions
- **No self-service tier**: The platform intentionally does not support client document uploads. All document processing happens locally on our infrastructure. This avoids SaaS privacy regulations (GDPR, data retention, breach notification). Clients only access read-only deliverables through the Vault. This is a deliberate compliance/liability decision, not a future feature.

---

## Risk Summary

Critical risks across all phases with mitigation strategies:

| Risk | Phase | Severity | Probability | Mitigation | Owner |
|------|-------|----------|-------------|------------|-------|
| **OCR quality <60% on handwritten docs** | 3 | HIGH | 70% | Route to Claude Vision API instead | Preprocessing |
| **Entity coreference merges wrong people** | 5 | HIGH | 40% | Conservative thresholds (≥0.85), human review queue | Graph |
| **Graph too large for frontend (>1500 nodes)** | 7 | MEDIUM | 50% | Default filtered views, performance warnings | Frontend |
| **LLM hallucinates entities not in document** | 4 | HIGH | 30% | Require evidence quotes, validate against OCR text | Extraction |
| **Batch processing <90% success rate** | 8 | MEDIUM | 40% | Robust error handling, manual review queue | Integration |
| **API costs exceed $10 for 300 docs** | 3-4 | LOW | 20% | Use Haiku by default, Sonnet only for retries | All |
| **Temporal conflicts unresolved** | 5 | MEDIUM | 50% | Implement precedence rules from SCHEMA.md | Graph |
| **Legal conclusions in output** | 4, 8 | CRITICAL | 10% | Manual review, prompt enforcement | QA |

**Risk Levels:**
- CRITICAL: Project-killing if not addressed
- HIGH: Major impact on quality or timeline
- MEDIUM: Moderate impact, workarounds exist
- LOW: Minor impact, easy to resolve

---

## Phase 1: Project Foundation

### Task 1.1: Python Project Structure

```bash
mkdir -p farmer_factory/{intake,prepare,extract,structure,export,config/prompts,utils}
mkdir -p cases
mkdir -p output
```

**requirements.txt:**
```
python-dotenv>=1.0.0
pydantic>=2.0.0
click>=8.1.0
opencv-python>=4.8.0
numpy>=1.24.0
scipy>=1.10.0
PyMuPDF>=1.23.0
Pillow>=10.0.0
google-cloud-vision>=3.4.0
anthropic>=0.18.0
networkx>=3.1
pyyaml>=6.0.0
```

### Task 1.2: Next.js Project

```bash
npx create-next-app@latest farmer_vault --typescript --tailwind --app
npm install react-force-graph-2d
```

### Task 1.3: Configuration

Create `config/settings.py` with paths, API keys, and processing configs.

### Task 1.4: CLI Framework

Create `cli.py` with Click commands:
- `create-case` - Initialize new case directory structure
- `process` - Process case documents through pipeline
- `upload` - Upload graph_data.json to Supabase Storage
- `export` - Export graph to local JSON

### Task 1.5: Supabase Integration

Set up Supabase project:
- Create Storage bucket: `case-graphs`
- Configure RLS policies for case isolation
- Set up database tables (cases, users, case_access, audit_logs)

---

## Phase 2: Preprocessing Pipeline

### Dependencies
- **Blocks:** Phase 3 (OCR needs preprocessed images)
- **External:** OpenCV, PyMuPDF installed
- **Data:** 10 sample documents for testing

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 2.0 | `prepare/triage.py` | Sample docs | MEDIUM | Correctly classifies 8/10 test docs by path |
| 2.1 | `prepare/page_extract.py` | PyMuPDF | LOW | Extracts all pages from test PDF at 300 DPI |
| 2.2 | `prepare/deskew.py` | OpenCV | LOW | Corrects rotation within ±0.5° on test images |
| 2.3 | `prepare/denoise.py` | OpenCV | LOW | Removes noise without losing text strokes |
| 2.4 | `prepare/enhance.py` | OpenCV | MEDIUM | Improves OCR-ability of faded documents |
| 2.5 | `prepare/binarize.py` | OpenCV | MEDIUM | Sauvola produces clean binary on handwritten samples |
| 2.6 | `prepare/segment.py` | OpenCV | HIGH | Detects text regions with 80%+ accuracy |
| 2.7 | `prepare/pipeline.py` | All above | LOW | Orchestrates full pipeline, logs triage stats |

**Acceptance Criteria (Phase):**
- ✅ Process 10 sample docs end-to-end
- ✅ Triage correctly identifies ~34% as typed, ~50% as handwritten
- ✅ Average processing time <3 min/doc
- ✅ No crashes on malformed PDFs

**Risks:**
- HIGH: Segment detection may fail on degraded documents → Mitigation: Make it optional, flag for review
- MEDIUM: Handwriting detection false positives → Mitigation: Allow manual override via config

---

## Phase 3: OCR Integration

### Dependencies
- **Blocks:** Phase 4 (Entity extraction needs OCR text)
- **External:** Google Cloud Vision API credentials
- **Prerequisite:** Phase 2 complete (preprocessed images available)

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 3.1 | `extract/ocr_engine.py` | GCV API, Phase 2 | MEDIUM | Returns OCR text with per-word confidence |
| 3.2 | `extract/ocr_postprocess.py` | OCR output | LOW | Normalizes dates, currency, Spanish characters |
| 3.3 | `extract/vision_model.py` | Claude Vision API | HIGH | Extracts entities from handwritten docs |

**Acceptance Criteria (Phase):**
- ✅ OCR 10 typed documents with avg confidence >80%
- ✅ Vision model extracts entities from 5 handwritten docs
- ✅ Error handling for API rate limits
- ✅ Confidence scores logged for each document

**Current Workaround (MVP1):**
- Vision API extraction is not yet implemented (stub only)
- **Use `--force-typed` flag** to route all documents through OCR + LLM path
- Google Cloud Vision OCR handles both typed and handwritten reasonably well
- Vision API implementation deferred to post-MVP (see "Out of Scope" section)

**Risks:**
- HIGH: Vision model may hallucinate entities → Mitigation: Cross-reference with multiple docs
- MEDIUM: API costs exceed budget → Mitigation: Use Haiku for simple docs, Sonnet for complex

---

## Phase 4: Entity & Relation Extraction

### Dependencies
- **Blocks:** Phase 5 (Graph construction needs entities)
- **External:** Anthropic API credentials
- **Prerequisite:** Phase 3 complete (OCR text available)

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 4.1 | `structure/schema.py` | SCHEMA.md | LOW | All Pydantic models validate against examples |
| 4.2 | `extract/entity_extractor.py` | Claude API, schema | MEDIUM | Achieves ≥75% precision on golden dataset |
| 4.3 | `extract/relation_extractor.py` | Entities, Claude API | MEDIUM | Achieves ≥70% precision on relations |
| 4.4 | `extract/summarizer.py` | Entities, relations | LOW | Generates factual summaries (no legal conclusions) |
| 4.5 | `extract/confidence_scorer.py` | All extractions | LOW | Assigns confidence based on OCR + extraction quality |
| 4.6 | `config/prompts/*.txt` | PROMPTS.md | LOW | All prompts match specification exactly |

**Acceptance Criteria (Phase):**
- ✅ Extract entities from 20-document golden dataset
- ✅ Entity precision ≥75%, recall ≥65%
- ✅ Relation precision ≥70%, recall ≥60%
- ✅ No legal conclusions in summaries (manual review)
- ✅ Confidence scores correlate with accuracy

**Risks:**
- HIGH: LLM extracts non-existent entities → Mitigation: Require evidence quotes, low confidence if not found
- MEDIUM: Prompt drift over time → Mitigation: Version prompts, regression test on golden set

---

## Phase 5: Graph Construction

### Dependencies
- **Blocks:** Phase 6 (Export needs graph)
- **Prerequisite:** Phase 4 complete (entities and relations extracted)

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 5.1 | `structure/graph_builder.py` | NetworkX, entities | LOW | Builds graph from entities, validates structure |
| 5.2 | `structure/resolver.py` | dedupe library, entities | HIGH | ML-based deduplication for all entity types (Person, Location, Property, Org) |
| 5.2a | `cli.py train-deduplication` | TEST-CERESA extractions | MEDIUM | Interactive training collects 20-30 labeled pairs per entity type |
| 5.2b | Trained dedupe models | Labeled training data | MEDIUM | Models saved to structure/models/, F1 score ≥70% |
| ~~5.3~~ | ~~`structure/gap_detector.py`~~ | ~~Complete graph, Claude API~~ | ~~MEDIUM~~ | **DEFERRED** to analyst workflow (see ADR 2026-01-23) |

**Acceptance Criteria (Phase):**
- ✅ Graph validates against SCHEMA.md structure
- ✅ <10% orphan nodes (isolated entities)
- ✅ Dedupe models trained on TEST-CERESA case (all 4 entity types)
- ✅ Deduplication F1 score ≥70% on test set
- ✅ Multi-attribute matching works (name + date + location)
- ✅ Confidence-weighted merging preserves data quality
- ~~✅ Gap detection identifies test case gaps~~ **DEFERRED** - Not needed for MVP1 family UI
- ✅ Temporal conflicts resolved per SCHEMA.md rules

**Risks:**
- HIGH: Dedupe merges wrong entities → Mitigation: Threshold ≥0.5, active learning with analyst feedback
- MEDIUM: Insufficient training data → Mitigation: Start with TEST-CERESA (18 docs), expand as more cases processed
- MEDIUM: Graph becomes too large (>1500 nodes) → Mitigation: Implement clustering in frontend
- LOW: Dedupe training time-consuming → Mitigation: 20-30 examples per type = ~15 min total training

---

## Phase 6: Narrative Generation

### Status: ✅ COMPLETE (redesigned 2026-01-28)

### Dependencies
- **Prerequisite:** Phase 5 complete (graph constructed)

### Overview
Batch case narrative generation during Factory processing. Produces `case_narrative.json` with per-period narratives organized by decade, case summary, and highlighted events. Delivered to the Vault as a static artifact (air gap maintained).

**Redesign (2026-01-28):** Replaced on-demand per-entity generation with batch per-case processing. See `docs/plans/2026-01-28-case-narrative-generation-redesign.md`.

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 6.1 | `narrative/models.py` | ✅ | Pydantic models: CaseNarrative, NarrativePeriod, NarrativeMetadata, EventHighlight |
| 6.2 | `narrative/prompts.py` | ✅ | Period + summary prompt templates with forensic voice |
| 6.3 | `narrative/generator.py` | ✅ | CaseNarrativeGenerator: decade grouping, sparse merge, cost tracking, model downgrade |
| 6.4 | CLI integration | ✅ | `generate-narrative` command + auto-run in `process` pipeline |
| 6.5 | Vault timeline API | ✅ | Reads case_narrative.json, merges into timeline response |
| 6.6 | Vault components | ✅ | TimelinePeriod renders narrative prose + highlighted events, page shows case_summary |
| 6.7 | Test suite | ✅ | 27 tests (models, prompts, generator) |

**Acceptance Criteria (Phase):**
- ✅ Batch per-case narrative generation (one run per case during processing)
- ✅ Period-based organization (decade grouping with sparse merge)
- ✅ Cost tracking with configurable limit ($2 default) and model downgrade (sonnet→haiku)
- ✅ Event highlighting (CONFISCATED, SOLD, INHERITED)
- ✅ Case summary generated from period narratives
- ✅ Output: `case_narrative.json` in case output directory
- ✅ Vault timeline API merges narrative into period responses
- ✅ Graceful degradation (timeline works without narrative file)
- ✅ 27 passing tests
- ✅ Design document

**Implementation Details:**
- **Architecture:** Batch generation during `process` pipeline (not on-demand)
- **Grouping:** Documents grouped by decade, adjacent sparse periods (<3 docs) merged
- **Cost Control:** Configurable max cost, model downgrade on failure, cost accumulation tracking
- **Output:** `case_narrative.json` with metadata, case_summary, and periods array
- **Vault:** Timeline API reads narrative file, merges into period response; handles missing file gracefully

**Test Coverage:**
```
tests/narrative/
├── test_models.py (6 tests) — serialization, defaults, roundtrip
├── test_prompts.py (6 tests) — constraints, highlighting, templates
└── test_generator.py (15 tests) — grouping, merge, cost guards, evidence
```

**Files:**
```
farmer_factory/
├── narrative/
│   ├── __init__.py
│   ├── models.py          # CaseNarrative, NarrativePeriod, NarrativeMetadata, EventHighlight
│   ├── prompts.py         # Period + summary prompt templates
│   └── generator.py       # CaseNarrativeGenerator (batch processing)
└── cli.py                 # generate-narrative command + process integration

farmer_vault/
├── app/api/cases/[caseId]/timeline/route.ts  # Reads case_narrative.json
├── app/case/[caseId]/narrative/page.tsx       # Renders case_summary
└── components/Narrative/TimelinePeriod.tsx     # Renders period narrative + events
```

**Removed (old on-demand architecture):**
- `narrative/scorer.py`, `constellation.py`, `cache.py`, `exceptions.py`
- `api/narrative.py`, `scripts/generate_narrative.py`
- `NarrativePanel.tsx`, `useNarrative.ts`, Vault narrative API route

---

## Phase 8A: Frontend MVP Demo ✅ COMPLETE (2026-01-25)

**Deliverables:**
- ✅ Next.js 14 app with App Router (16.1.4 with Turbopack)
- ✅ Force-directed graph visualization (react-force-graph-2d)
- ✅ Entity sidebar (details panel with API-fetched data)
- ✅ Narrative timeline (batch-generated, rendered per-period)
- ✅ Dark theme with verification tier colors
- ✅ Error boundary for production resilience
- ✅ Comprehensive test suite (12 passing tests)

**Implementation:** See `docs/plans/2026-01-25-frontend-mvp-implementation-plan.md`

**Key Features:**
- Server/client component split for optimal performance
- React.cache() for request deduplication
- SWR for client-side caching
- Dynamic imports (~200KB bundle reduction)
- ARIA-compliant accessibility (WCAG AA)
- Pulsing glow on selected graph nodes

**Limitations:**
- Local development only (no authentication yet)
- Single case (TEST-CERESA hardcoded)
- File-based graph data (no Supabase integration yet)

**Next Steps:** Phase 8B for authentication and database integration

---

## Phase 8A.1: Document-First Frontend ✅ COMPLETE (2026-01-26)

**Deliverables:**
- ✅ Document-first navigation architecture
- ✅ Sidebar navigation (Dashboard, Documents, Entities, Narrative, Graph)
- ✅ Dashboard with real-time metrics and workflow tracking
- ✅ Entity browser with type-based grouping
- ✅ Timeline view with decade-based document grouping
- ✅ API routes for all data views
- ✅ Tests passing (12 tests)

**Implementation:** See `docs/plans/2026-01-26-document-first-frontend-redesign.md`

**New API Routes:**
- `/api/cases/[caseId]/dashboard` - Aggregated metrics, verification distribution
- `/api/cases/[caseId]/entities` - Entities grouped by type
- `/api/cases/[caseId]/timeline` - Documents grouped by decade
- `/api/cases/[caseId]/graph` - Full graph data

**New Components:**
- `EntityBrowser` - Type-grouped entity display
- `TimelinePeriod` - Expandable timeline periods
- `GraphView` - Knowledge graph wrapper with navigation
- `WorkflowChecklist` - Workflow stage tracking

**Key Features:**
- Contextual Cuban history titles for timeline periods (e.g., "Expropriation Period")
- AI disclaimer banners for TIER_3_AI data
- Verification status bar with tier breakdown
- Workflow progression tracking
- Click-through navigation between views

**Architecture:**
```
/case/[caseId]/              → Dashboard (metrics, workflow)
/case/[caseId]/documents     → Document Browser
/case/[caseId]/entities      → Entity Browser (by type)
/case/[caseId]/narrative     → Timeline View (by decade)
/case/[caseId]/graph         → Knowledge Graph
```

**Next Steps:** Phase 8A.2 for Forensic Dossier PDF export

---

## Phase 8A.2: Forensic Dossier Export (LaTeX)

### Status: ✅ COMPLETE (2026-01-27)

### Overview
Professional PDF dossier generation using LaTeX templates. This is the primary client deliverable — a polished, legal-ready document that justifies the consulting fee.

**Design Document:** `docs/plans/2026-01-27-latex-dossier-module-design.md`

### Dependencies
- **Prerequisite:** Phase 8A.1 complete (document-first data model)
- **External:** LaTeX distribution (MacTeX on macOS, TeX Live on Linux)
- **Data:** KnowledgeGraph + extractions/*.json

### Key Design Decisions
- **Dual narrative spine:** Family-centric AND Property-centric (both equally important)
- **Modular sections:** Include/exclude per case needs
- **English only (MVP):** Spanish support as future enhancement
- **Text-only (MVP):** No embedded images, maps optional via geolocation module
- **Hybrid executive summary:** Template extracts facts, LLM polishes prose
- **Verification handling:** Global disclaimer + per-section indicators

### Dossier Structure
```
1. FRONT MATTER
   - Executive Summary (2-paragraph, LLM-polished)
   - Disclaimer & Methodology
   - Table of Contents

2. COMPLETE TIMELINE
   - Chronological list of all events (family + property)
   - Dates, event type, summary, source document

3. THE FAMILY
   - Family origins and lineage
   - Key figures (who owned, who inherits)
   - Family tree (text-based for MVP)

4. THE PROPERTY
   - Property description and location
   - Historical context
   - Map placeholder (optional — from geolocation module)

5. OWNERSHIP HISTORY (narrative spine)
   - Acquisition: How the family came to own it
   - Ownership period: Key events during tenure
   - Confiscation/Loss: The taking (with evidence)

6. EVIDENCE INVENTORY
   - Document-by-document summary
   - What each document proves
   - Verification status per document

7. APPENDIX
   - Full citations
   - Methodology notes
   - Glossary (Spanish legal terms)
```

### Data Flow
```
KnowledgeGraph (graph_data.json)
        +
extractions/*.json (for evidence quotes)
        ↓
    DossierPreparer → DossierData (Pydantic)
        ↓
    DossierRenderer (Jinja2 → .tex)
        ↓
    DossierCompiler (pdflatex → PDF)
        ↓
    {case_id}_dossier.pdf
```

### Tasks

| Task | File | Dependencies | Acceptance Criteria |
|------|------|--------------|---------------------|
| 8A.2.1 | `dossier/models.py` | Pydantic | DossierData and all section sub-models defined |
| 8A.2.2 | `dossier/templates/*.tex.j2` | Jinja2 | All 7 section templates created |
| 8A.2.3 | `dossier/renderer.py` | Jinja2, templates | Renders DossierData to .tex with LaTeX escaping |
| 8A.2.4 | `dossier/compiler.py` | pdflatex | Compiles .tex to PDF, handles errors |
| 8A.2.5 | `dossier/preparer.py` | KnowledgeGraph, extractions | Assembles DossierData from case artifacts |
| 8A.2.6 | `dossier/styles/civictable.sty` | LaTeX | Custom style (fonts, colors, headers) |
| 8A.2.7 | `cli.py generate-dossier` | All above | CLI command generates PDF |
| 8A.2.8 | Test with TEST-CERESA | Full pipeline | End-to-end PDF generation works |

### Module Structure
```
farmer_factory/dossier/
├── __init__.py           # Public API: generate_dossier()
├── models.py             # DossierData and section sub-models
├── preparer.py           # Assembles DossierData from case artifacts
├── renderer.py           # Jinja2 → LaTeX rendering
├── compiler.py           # pdflatex compilation
├── templates/
│   ├── main.tex.j2              # Document skeleton
│   ├── sections/
│   │   ├── front_matter.tex.j2
│   │   ├── timeline.tex.j2
│   │   ├── family.tex.j2
│   │   ├── property.tex.j2
│   │   ├── ownership.tex.j2
│   │   ├── documents.tex.j2
│   │   └── appendix.tex.j2
│   └── partials/
│       ├── verification_badge.tex.j2
│       ├── citation.tex.j2
│       └── event_row.tex.j2
└── styles/
    └── civictable.sty
```

### Technical Approach

**Template Engine:** Jinja2 with custom delimiters (avoid LaTeX conflicts)
```python
env = Environment(
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='<<',
    variable_end_string='>>',
)
```

**Compilation:**
```bash
pdflatex -interaction=nonstopmode dossier.tex
pdflatex -interaction=nonstopmode dossier.tex  # Run twice for TOC
```

### Acceptance Criteria
- ✅ CLI command `generate-dossier CASE-ID --property-id X --family-member-id Y` generates PDF
- ✅ PDF renders correctly with all 7 sections
- ✅ Timeline displays all events chronologically
- ✅ Family tree shows lineage correctly
- ✅ Ownership history tells coherent narrative
- ✅ Verification tiers display with appropriate styling
- ✅ No legal conclusions in any generated text
- ✅ Methodology disclaimer present and prominent
- ✅ Professional appearance suitable for legal proceedings

### Implementation Details
- **Template Engine:** Jinja2 with custom delimiters (`<%`, `%>`, `<<`, `>>`) to avoid LaTeX conflicts
- **LaTeX Style:** Custom `civictable.sty` with Palatino fonts and professional formatting
- **Data Contract:** Pydantic models (DossierData, FamilyData, PropertyData, etc.)
- **Compilation:** Two-pass pdflatex for TOC generation
- **Architecture Fix:** Added DOCUMENT entity creation in `builder.py`
- **Architecture Fix:** Updated `PROMPTS.md` to use specific family relation types (CHILD_OF, SPOUSE_OF, HEIR_OF)
- **Frontend Fix:** Added DOCUMENT entity support to GraphView, EntityBrowser, EntityDetail

### Files Created
```
farmer_factory/dossier/
├── __init__.py
├── models.py
├── preparer.py
├── renderer.py
├── compiler.py
├── templates/
│   ├── main.tex.j2
│   ├── sections/*.tex.j2 (7 sections)
│   └── partials/*.tex.j2 (3 partials)
└── styles/
    └── civictable.sty
```

### CLI Commands Added
- `list-entities CASE-ID [--type TYPE]` - List entities in a case
- `generate-dossier CASE-ID [--property-id X] [--person-id Y] [--dry-run]` - Generate PDF dossier

**Next Steps:** Phase 8A.3 for Geolocation Module

---

## Phase 8A.3: Property Geolocation Module

### Status: 🔲 PLANNED (Future Enhancement)

### Overview
Separate module for generating map images showing exact property boundaries and location. Integrates with dossier as optional enhancement.

**Design Document:** `docs/plans/2026-01-27-latex-dossier-module-design.md` (Future Enhancements section)

### Dependencies
- **Prerequisite:** Phase 8A.2 complete (dossier can function without maps)
- **External:** Mapping API (Mapbox, Google Static Maps, or OpenStreetMap)
- **Data:** PropertyData with address, cadastral_info, area fields

### Why Separate Module
- Keeps dossier module focused on document generation
- Geolocation is optional — dossier degrades gracefully without it
- Different technical concerns (API calls, map rendering, caching)
- Can be developed/tested independently

### Planned Capabilities
1. **Geocoding** — Convert historical Cuban addresses to coordinates
2. **Boundary rendering** — Paint exact property area/boundaries on map
3. **Static map generation** — Output PNG/PDF images for dossier embedding
4. **Backend logging** — Track all geolocation requests and results

### Technical Considerations
- Historical Cuban addresses may not exist in modern geocoding APIs
- May need cadastral records or historical maps as reference
- Possible APIs: Mapbox Static Images, Google Static Maps, OpenStreetMap
- Property boundaries derived from `area`, `cadastral_info`, `registry_number` fields

### Module Structure
```
farmer_factory/geolocation/
├── __init__.py
├── models.py           # GeolocationResult, PropertyBounds
├── geocoder.py         # Address → coordinates
├── renderer.py         # Coordinates → map image
├── cache.py            # Cache geocoding results
└── logging.py          # Backend request/result logging
```

### Data Flow
```
PropertyData (address, cadastral_info, area)
        ↓
    geocoder.py → coordinates
        ↓
    renderer.py → map image (PNG)
        ↓
    Saved to cases/{case_id}/output/maps/
        ↓
    Referenced in DossierData.property.map_image_path
```

### Dossier Integration
Templates include conditional map display:
```latex
<% if d.property.map_image_path %>
\includegraphics[width=\textwidth]{<< d.property.map_image_path >>}
<% else %>
\textit{Map not available. See property description above.}
<% endif %>
```

### Tasks

| Task | File | Dependencies | Acceptance Criteria |
|------|------|--------------|---------------------|
| 8A.3.1 | `geolocation/models.py` | Pydantic | GeolocationResult, PropertyBounds models |
| 8A.3.2 | `geolocation/geocoder.py` | Mapping API | Converts Cuban addresses to coordinates |
| 8A.3.3 | `geolocation/renderer.py` | Static Maps API | Generates PNG with property boundary |
| 8A.3.4 | `geolocation/cache.py` | Redis/file | Caches geocoding results |
| 8A.3.5 | `geolocation/logging.py` | Logging | Tracks all requests and results |
| 8A.3.6 | `cli.py generate-map` | All above | CLI command generates property map |
| 8A.3.7 | Dossier integration | Phase 8A.2 | Maps appear in PDF when available |

### Acceptance Criteria
- ✅ CLI command `generate-map CASE-ID --property-id X` generates PNG
- ✅ Map shows property location accurately
- ✅ Property boundaries rendered when data available
- ✅ All geocoding requests logged for audit
- ✅ Dossier includes map when available, graceful fallback when not
- ✅ Caching prevents redundant API calls

**Next Steps:** Phase 8B for authentication and database integration

---

## Phase 8B: Client Intake & Case Tracking (Future)

### Status: 🔲 DEFERRED (Post-MVP)

### Overview
Operational tooling for managing client intake and case lifecycle. Not in MVP — use external tools (Typeform, Google Drive, Notion) initially.

### When to Build
- After 10+ cases processed manually
- When external tools become friction
- When patterns emerge for what's actually needed

### Potential Scope
- Intake form (family info, known properties, document inventory)
- Client communication templates
- Case status tracking
- Document submission workflow (still local processing, not upload)
- Invoice/payment tracking integration

### Tools for MVP1 (No Code)
| Function | Tool | Notes |
|----------|------|-------|
| Initial inquiry | Calendly | Schedule discovery calls |
| Intake form | Typeform/Google Forms | Collect family info |
| Document submission | Google Drive shared folder | Client uploads scans |
| Case tracking | Notion database | Status, notes, deadlines |
| Communication | Email + Loom | Updates and walkthroughs |
| Invoicing | Stripe/PayPal | Manual for now |

---

## Phase 7: Export & CLI

### Dependencies
- **Blocks:** Phase 8 (Frontend needs graph_data.json)
- **Prerequisite:** Phase 6 complete (narrative generation available)

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 6.1 | `export/json_exporter.py` | Graph, SCHEMA.md | LOW | Outputs valid graph_data.json |
| 6.2 | `export/audit_log.py` | All processing steps | LOW | Complete audit trail in JSON Lines format |
| 6.3 | `utils/supabase_uploader.py` | Supabase SDK | MEDIUM | Uploads graph to Supabase Storage with RLS |
| 6.4 | `cli.py` | Click, all modules | LOW | CLI has create-case, process, upload commands |
| 6.5 | `main.py` | All modules | LOW | Orchestrates full pipeline with error handling |

**Acceptance Criteria (Phase):**
- ✅ graph_data.json validates against JSON schema
- ✅ Audit log captures all processing steps with hashes
- ✅ CLI can create case with `create-case` command
- ✅ CLI can process 1 doc in <5 min
- ✅ Batch mode processes 10 docs unattended
- ✅ CLI uploads graph to Supabase Storage with `upload` command
- ✅ RLS prevents cross-case access
- ✅ Graceful error handling (no crashes)

**Risks:**
- LOW: JSON too large for frontend → Mitigation: Implement compression, paginate if needed

---

## Phase 8: Frontend + Authentication

### Dependencies
- **Blocks:** Phase 9 (Integration testing needs UI)
- **Prerequisite:** Phase 7 complete (graph_data.json available)

### Tasks

| Task | File | Dependencies | Risk | Acceptance Criteria |
|------|------|--------------|------|---------------------|
| 7.1 | Clerk setup | None | LOW | Clerk account created, app configured |
| 7.2 | `middleware.ts` | @clerk/nextjs | LOW | Routes protected, redirects to sign-in |
| 7.3 | `app/sign-in/[[...sign-in]]/page.tsx` | Clerk | LOW | Sign-in flow works, MFA prompts |
| 7.4 | Webhook for user sync | Supabase | MEDIUM | Clerk users auto-sync to Supabase |
| 7.5 | Database schema + RLS | Supabase | HIGH | Case isolation verified (user A cannot see user B) |
| 7.6 | `globals.css`, `tailwind.config.js` | None | LOW | Dark theme renders correctly |
| 7.7 | `lib/types.ts` | SCHEMA.md | LOW | TypeScript types match Pydantic models |
| 7.8 | `components/KnowledgeGraph.tsx` | react-force-graph-2d | MEDIUM | Renders 500 nodes at 40+ FPS |
| 7.9 | `components/GraphFilterTabs.tsx` | types | LOW | Tabbed filters work (overview, families, properties, etc.) |
| 7.10 | `components/DossierPanel.tsx` | types | LOW | Shows entity details, sources, relations |
| 7.11 | `components/NodeBadge.tsx` | types | LOW | Verification tier badges display |
| 7.12 | `app/case/[id]/page.tsx` | All components, auth | MEDIUM | Dashboard integrates all components, requires login |
| 7.13 | `app/api/cases/[id]/graph/route.ts` | Supabase Storage | MEDIUM | Fetches graph from Supabase with RLS |
| 7.14 | `app/api/cases/[id]/verify-entity/route.ts` | Supabase | MEDIUM | Promotes entity to TIER_2_ANALYST |
| 7.15 | `components/AnalystReviewPanel.tsx` | types, API | MEDIUM | Analyst can review and verify entities |
| 7.16 | `lib/audit.ts` | Supabase | LOW | Audit logging utility works |
| 7.17 | Security headers | next.config.js | LOW | HSTS, CSP, X-Frame-Options set |
| 7.18 | PostHog setup | None | LOW | Analytics initialized, tracking family usage |
| 7.19 | Sentry setup | None | LOW | Error tracking configured for frontend |
| 7.20 | Analytics instrumentation | PostHog | LOW | Key user actions tracked (graph interactions, filters) |

**Acceptance Criteria (Phase):**
- ✅ Cannot access /case/* without authentication
- ✅ Sign-in flow works (email + MFA)
- ✅ Users auto-sync from Clerk to Supabase
- ✅ RLS prevents cross-case access (tested)
- ✅ Graph fetched from Supabase Storage (not local file)
- ✅ Graph renders test dataset (300 nodes)
- ✅ Filtered views reduce to <300 nodes
- ✅ Node click shows dossier panel
- ✅ Analyst can verify entities (TIER_3_AI → TIER_2_ANALYST)
- ✅ Verification updates graph in real-time
- ✅ Legal disclaimer present and prominent
- ✅ All verification tiers display correctly
- ✅ Document access logged to audit table
- ✅ Responsive on desktop (no mobile requirement MVP1)
- ✅ PostHog tracking family usage (graph interactions, filter usage, session duration)
- ✅ Sentry capturing frontend errors with context

**Risks:**
- HIGH: RLS misconfiguration leaks data → Mitigation: Extensive testing with multiple users
- MEDIUM: Performance issues with large graphs → Mitigation: Default to filtered view, add performance warnings
- MEDIUM: Webhook delays in user sync → Mitigation: Retry logic, manual sync fallback
- LOW: Design not polished → Acceptable for MVP1, iterate based on feedback

---

## Phase 9: Integration Testing

### Dependencies
- **Prerequisite:** All phases 1-8 complete

### Tasks

| Task | Description | Dependencies | Risk | Acceptance Criteria |
|------|-------------|--------------|------|---------------------|
| 8.1 | Process 10-doc test set | Full pipeline | MEDIUM | End-to-end success, graph validates |
| 8.2 | Quality validation | Golden dataset | LOW | Meets all error budgets from ARCHITECTURE.md |
| 8.3 | Frontend testing | Browser, graph_data.json | LOW | UI functional, no console errors |
| 8.4 | Full batch (300 docs) | Production data | HIGH | Completes in <50 hours, <10% failures |

**Acceptance Criteria (Phase):**
- ✅ 10-doc test: 100% success rate
- ✅ Quality metrics meet targets (precision ≥75%, recall ≥65%)
- ✅ Frontend renders without errors
- ✅ 300-doc batch: ≥90% automated processing rate
- ✅ Audit trail complete for all documents
- ✅ No legal conclusions in output (manual review)

**Risks:**
- HIGH: Batch processing reveals edge cases → Mitigation: Robust error handling, flag for manual review
- MEDIUM: Quality below targets → Mitigation: Tune prompts, adjust thresholds, acceptable for MVP1

---

## File Checklist

### Factory (Python)
```
farmer_factory/
├── cli.py                    [ ] # Added: create-case, upload commands
├── main.py                   [ ]
├── requirements.txt          [ ] # Added: supabase-py
├── config/
│   ├── settings.py           [ ]
│   └── prompts/*.txt         [ ]
├── intake/
│   └── pdf_loader.py         [ ]
├── prepare/
│   ├── page_extract.py       [ ]
│   ├── deskew.py             [ ]
│   ├── denoise.py            [ ]
│   ├── enhance.py            [ ]
│   ├── binarize.py           [ ]
│   ├── segment.py            [ ]
│   └── pipeline.py           [ ]
├── extract/
│   ├── ocr_engine.py         [ ]
│   ├── ocr_postprocess.py    [ ]
│   ├── entity_extractor.py   [ ]
│   ├── relation_extractor.py [ ]
│   ├── summarizer.py         [ ]
│   ├── chunker.py            [✓] # Document text chunking (5000-char, 10% overlap)
│   ├── parsers.py            [✓] # NEW - Response parsing and entity transformation
│   └── prompts/              [✓] # NEW - Prompt builders package
│       ├── __init__.py       [✓]
│       ├── helpers.py        [✓] # Domain-aware helpers
│       ├── zero_shot.py      [✓] # Zero-shot prompts (default)
│       └── few_shot.py       [✓] # Few-shot prompts (reference only)
├── structure/
│   ├── schema.py             [✓] # Complete (includes LocationNature, OrganizationNature enums)
│   ├── graph_builder.py      [✓] # Complete (integrates postprocessor)
│   ├── resolver.py           [✓] # Complete - Dedupe-based entity resolution
│   ├── postprocessor.py      [✓] # NEW - Graph post-processing (transitive redundancy, validation)
│   ├── merge_models.py       [✓] # NEW - Pydantic models for merge authority YAML
│   ├── merge_writer.py       [✓] # NEW - Write entity group YAML files
│   ├── merge_reader.py       [✓] # NEW - Read entity groups, get merge maps
│   ├── merge_engine.py       [✓] # NEW - Graph surgery engine (apply_merges)
│   ├── models/               [ ] # Trained dedupe models (*.pkl)
│   └── ~~gap_detector.py~~   [x] # DEFERRED to analyst workflow
├── narrative/                [✓] # Batch case narrative generation
│   ├── __init__.py           [✓]
│   ├── models.py             [✓] # CaseNarrative, NarrativePeriod, NarrativeMetadata, EventHighlight
│   ├── prompts.py            [✓] # Period + summary prompt templates
│   └── generator.py          [✓] # CaseNarrativeGenerator (batch processing)
├── export/
│   ├── json_exporter.py      [ ]
│   └── audit_log.py          [ ]
├── dossier/                  [✓] # PDF dossier generation module (Phase 8A.2)
│   ├── __init__.py           [✓]
│   ├── models.py             [✓] # DossierData and section sub-models
│   ├── preparer.py           [✓] # Assembles DossierData from case artifacts
│   ├── renderer.py           [✓] # Jinja2 → LaTeX rendering
│   ├── compiler.py           [✓] # pdflatex compilation
│   ├── templates/
│   │   ├── main.tex.j2       [✓]
│   │   ├── sections/
│   │   │   ├── front_matter.tex.j2   [✓]
│   │   │   ├── timeline.tex.j2       [✓]
│   │   │   ├── family.tex.j2         [✓]
│   │   │   ├── property.tex.j2       [✓]
│   │   │   ├── ownership.tex.j2      [✓]
│   │   │   ├── documents.tex.j2      [✓]
│   │   │   └── appendix.tex.j2       [✓]
│   │   └── partials/
│   │       ├── verification_badge.tex.j2 [✓]
│   │       ├── citation.tex.j2       [✓]
│   │       └── event_row.tex.j2      [✓]
│   └── styles/
│       └── civictable.sty    [✓]
├── geolocation/              [ ] # NEW - Property mapping module (future)
│   ├── __init__.py           [ ]
│   ├── models.py             [ ] # GeolocationResult, PropertyBounds
│   ├── geocoder.py           [ ] # Address → coordinates
│   ├── renderer.py           [ ] # Coordinates → map image
│   ├── cache.py              [ ] # Cache geocoding results
│   └── logging.py            [ ] # Backend request/result logging
└── utils/                    [ ] # NEW
    ├── retry.py              [ ] # NEW - Retry with backoff
    ├── cost_tracker.py       [ ] # NEW - API cost logging
    └── supabase_uploader.py  [ ] # NEW - Upload to Supabase Storage

tests/
├── extract/
│   └── test_chunker.py       [✓] # Document chunking tests (9 tests)
├── structure/
│   ├── test_postprocessor.py [✓] # Post-processing tests (9 tests)
│   ├── test_merge_models.py  [✓] # Merge model tests (17 tests)
│   ├── test_merge_writer.py  [✓] # Merge writer tests (9 tests)
│   ├── test_merge_reader.py  [✓] # Merge reader tests (10 tests)
│   └── test_merge_engine.py  [✓] # Merge engine tests (18 tests)
├── golden/                   [✓] # Golden standard evaluation
│   ├── __init__.py
│   ├── data/
│   │   ├── sample_escritura.txt
│   │   └── expected_extraction.json
│   └── test_golden_evaluation.py  # Extraction quality tests (7 tests)
└── ...                       # Existing test modules
```

### Vault (Next.js)
```
farmer_vault/
├── middleware.ts             [ ] # Clerk auth middleware
├── app/
│   ├── layout.tsx            [ ] # ClerkProvider wrapper
│   ├── globals.css           [ ]
│   ├── sign-in/[[...sign-in]]/page.tsx [ ] # Clerk sign-in
│   ├── sign-up/[[...sign-up]]/page.tsx [ ] # Clerk sign-up
│   ├── api/
│   │   ├── webhook/
│   │   │   └── clerk/route.ts [ ] # User sync webhook
│   │   └── cases/
│   │       └── [id]/
│   │           ├── graph/route.ts [ ] # NEW - Fetch graph from Supabase
│   │           ├── verify-entity/route.ts [ ] # NEW - Analyst verification
│   │           └── dossier/route.ts [ ] # NEW - PDF dossier download
│   └── case/[id]/page.tsx    [ ]
├── components/
│   ├── Graph/
│   │   ├── KnowledgeGraph.tsx    [✓]
│   │   ├── GraphView.tsx         [✓]
│   │   ├── EntitySidebar.tsx     [✓]
│   │   ├── GraphSettingsPanel.tsx [✓]
│   │   └── NodeBadge.tsx         [✓]
│   ├── Narrative/
│   │   └── TimelinePeriod.tsx    [✓]
│   ├── Dashboard/
│   │   ├── Header.tsx            [✓]
│   │   └── DossierDownload.tsx   [✓]
│   ├── Documents/
│   │   ├── DocumentViewer.tsx    [✓]
│   │   └── DocumentList.tsx      [✓]
│   ├── Entities/
│   │   ├── EntityDetail.tsx      [✓]
│   │   └── EntityBrowser.tsx     [✓]
│   └── shared/
│       ├── Header.tsx            [✓]
│       ├── Sidebar.tsx           [✓]
│       ├── ErrorBoundary.tsx     [✓]
│       ├── ErrorState.tsx        [✓]
│       ├── LoadingState.tsx      [✓]
│       ├── VerificationBadge.tsx [✓]
│       └── Card.tsx              [✓]
├── lib/
│   ├── types.ts              [ ]
│   ├── graph-config.ts       [ ]
│   ├── audit.ts              [ ] # Audit logging utility
│   ├── supabase.ts           [ ] # Supabase client
│   ├── analytics.ts          [ ] # NEW - PostHog integration
│   └── sentry.ts             [ ] # NEW - Sentry error tracking
└── public/
    # NO public/data/ - graphs fetched from Supabase Storage
```

---

## Implementation Order

1. **Foundation** — Project structure, deps, config
2. **Schema** — Pydantic models (ensures type safety)
3. **Preprocessing** — Build/test each stage
4. **OCR** — Google Cloud integration
5. **Extraction** — Claude API prompts
6. **Graph** — NetworkX construction
7. **Export/CLI** — Complete backend
8. **Frontend** — Next.js components
9. **Integration** — End-to-end testing

---

## Environment Variables

```bash
# .env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
```

---

## Phase 9: Domain Configuration Abstraction

### Status: 🟡 IN PROGRESS (Infrastructure Complete, Integration Pending)

### Overview
Abstract Cuban-specific elements into a configuration layer, enabling the platform to serve multiple domains (genealogy, academic research, investigative journalism, parallel restitution claims).

**Design Document:** `docs/architecture/DOMAIN_CONFIGURATION.md`
**Strategic Document:** `docs/strategy/CIVIC_ARCHITECTURE_VISION.md`

### Why This Matters
- **70% of the platform is domain-agnostic** — only entity types, relation types, prompts, and success criteria need configuration
- **Market expansion** — Genealogy ($4.7B market), academic/DH, investigative journalism
- **Methodology publication** — Document at general level, with Cuban property as case study
- **Competitive moat** — No one else has end-to-end documentary recovery infrastructure

### Implementation Status

**✅ COMPLETE - Infrastructure (2026-01-27):**
```
farmer_factory/domains/
├── __init__.py              ✅ Public API exports
├── models.py                ✅ Pydantic models for domain configs
├── loader.py                ✅ YAML loader with caching
├── registry.py              ✅ Singleton registry for active domain
├── cuban_property/
│   ├── __init__.py          ✅
│   ├── domain.yaml          ✅ Domain manifest (name, version, scope)
│   ├── entities.yaml        ✅ 5 entity types, 39 total fields
│   ├── relations.yaml       ✅ 28 relation types with categories
│   └── prompts/
│       └── system_context.txt ✅ Cuban-specific extraction context
└── base/
    └── verification.yaml    ✅ 4-tier verification system
```

**🔲 PENDING - Integration:**
- Refactor `extract/llm.py` to use domain prompts
- Refactor `structure/schema.py` for dynamic entity/relation types
- Add `--domain` CLI flag
- Update tests to be domain-aware

### Elements Abstracted

| Element | Status | Location |
|---------|--------|----------|
| **Entity types** | ✅ | `domains/cuban_property/entities.yaml` |
| **Entity fields** | ✅ | `domains/cuban_property/entities.yaml` |
| **Relation types** | ✅ | `domains/cuban_property/relations.yaml` |
| **Extraction context** | ✅ | `domains/cuban_property/prompts/system_context.txt` |
| **Verification tiers** | ✅ | `domains/base/verification.yaml` |
| **Known entities** | ✅ | In entities.yaml (INRA, locations, etc.) |
| **Extraction hints** | ✅ | Per-field and per-relation hints |

### Implemented Structure

```
farmer_factory/domains/
├── __init__.py              # domain_registry, DomainLoader, DomainConfig
├── models.py                # FieldDefinition, EntityTypeConfig, RelationTypeConfig, DomainConfig
├── loader.py                # DomainLoader (YAML parsing, caching)
├── registry.py              # DomainRegistry singleton
│
├── cuban_property/          # Cuban Property Restitution domain
│   ├── domain.yaml          # name, version, language, temporal/geographic scope
│   ├── entities.yaml        # PERSON (14 fields), PROPERTY (9), ORGANIZATION (3), LOCATION (4), DOCUMENT (9)
│   ├── relations.yaml       # 28 relation types in 11 categories
│   └── prompts/
│       └── system_context.txt
│
└── base/                    # Shared across domains
    └── verification.yaml    # TIER_3_AI, TIER_2_ANALYST, TIER_2_INSTITUTIONAL, TIER_1_CERTIFIED
```

### Domain Configuration Schema

```yaml
# domains/cuban_property/schema.yaml
domain:
  name: "Cuban Property Restitution"
  code: "cuban_property"
  version: "1.0.0"
  language: "es"  # Primary document language
  temporal_range: "1940-1965"

entity_types:
  PERSON:
    fields:
      - name: name
        type: string
        required: true
      - name: alternate_names
        type: list[string]
      - name: birth_date
        type: date
      - name: mother
        type: string
        description: "Name of mother (from 'hijo de' phrases)"
      # ... more fields

  PROPERTY:
    fields:
      - name: name
        type: string
      - name: property_type
        type: enum
        values: [finca, hacienda, ingenio, urban, commercial]
      - name: registry_number
        type: string
      # ... more fields

relation_types:
  - type: OWNS
    source: [PERSON, ORGANIZATION]
    target: [PROPERTY]
    temporal: true

  - type: CONFISCATED
    source: [ORGANIZATION]  # Government
    target: [PROPERTY]
    temporal: true

  - type: CHILD_OF
    source: [PERSON]
    target: [PERSON]
    symmetric: false

verification:
  criteria:
    TIER_2_ANALYST:
      description: "Civic Table analyst verified against source documents"
      requirements:
        - "Entity appears in at least one source document"
        - "Key attributes match document text"
    TIER_1_CERTIFIED:
      description: "FCSC claim accepted or legal certification"
      external: true

success_definition:
  primary_goal: "FCSC claim preparation"
  secondary_goals:
    - "Lawyer negotiation leverage"
    - "Family historical record"
```

### Tasks

| Task | Description | Dependencies | Acceptance Criteria |
|------|-------------|--------------|---------------------|
| 9.1 | Design domain config schema | CIVIC_ARCHITECTURE_VISION.md | YAML schema handles Cuban case fully |
| 9.2 | Extract Cuban-specific elements | Current schema.py, PROMPTS.md | All hardcoded Cuban elements identified |
| 9.3 | Create domain loader | Pydantic, YAML | Loads and validates domain configs |
| 9.4 | Refactor extraction prompts | Current prompts | Prompts use domain config context |
| 9.5 | Refactor schema.py | Domain loader | Entity/relation types from config |
| 9.6 | Create cuban_property domain | All above | MVP functionality preserved |
| 9.7 | Create genealogy domain (pilot) | Domain framework | Basic genealogy schema works |
| 9.8 | Documentation | All above | DOMAIN_CONFIGURATION.md complete |

### Acceptance Criteria
- ✅ Cuban property domain config fully specifies current behavior
- ✅ Core modules load entity/relation types from domain config
- ✅ Extraction prompts parameterized by domain
- ✅ MVP1 functionality unchanged when using cuban_property domain
- ✅ Can create new domain by writing config files (no code changes)
- ✅ Genealogy pilot domain processes test documents
- ✅ Documentation explains how to add new domains

### Risks
- MEDIUM: Config complexity becomes unwieldy → Mitigation: Start simple, add features as needed
- LOW: Breaking changes to MVP → Mitigation: Domain config should produce identical behavior for Cuban case

---

## Phase 9A.1: LLM Extraction Refactor

### Status: ✅ COMPLETE (2026-01-27)

### Overview
Refactored the 1557-line `llm.py` into smaller modules and implemented zero-shot prompts based on Chilean KG paper methodology (arXiv:2408.11975). A/B testing showed zero-shot extracts more entities while being ~50% cheaper.

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 9A.1.1 | `prompts/__init__.py` | ✅ | Package initialization |
| 9A.1.2 | `prompts/helpers.py` | ✅ | Domain-aware helper functions |
| 9A.1.3 | `prompts/few_shot.py` | ✅ | Original few-shot prompts (kept for reference) |
| 9A.1.4 | `prompts/zero_shot.py` | ✅ | Zero-shot prompts (~50% shorter) |
| 9A.1.5 | `parsers.py` | ✅ | Response parsing and entity transformation |
| 9A.1.6 | `llm.py` refactor | ✅ | Reduced from 1557 to ~750 lines |
| 9A.1.7 | `models.py` fix | ✅ | Null coercion for list fields and TemporalInfo.ongoing |
| 9A.1.8 | Zero-shot as default | ✅ | Removed prompt_mode parameter |
| 9A.1.9 | Manifest generation | ✅ | Added to processing pipeline |
| 9A.1.10 | CLI generate-manifest | ✅ | For existing processed cases |

### Key Results
- **Zero-shot extracted 6x more entities** than few-shot in A/B testing
- **~50% cost reduction** from shorter prompts
- **Cleaner architecture** with separation of concerns
- **Fixed null coercion bugs** that caused validation errors

### Files Created/Modified
```
farmer_factory/extract/
├── prompts/
│   ├── __init__.py       ✅ NEW
│   ├── helpers.py        ✅ NEW
│   ├── few_shot.py       ✅ NEW
│   └── zero_shot.py      ✅ NEW
├── parsers.py            ✅ NEW
├── llm.py                ✅ MODIFIED (refactored)
├── models.py             ✅ MODIFIED (null coercion)
└── __init__.py           ✅ MODIFIED (exports)

farmer_factory/processing/
└── pipeline.py           ✅ MODIFIED (manifest generation)

farmer_factory/cli.py     ✅ MODIFIED (generate-manifest command)

tests/extract/
├── test_prompts.py       ✅ NEW (10 tests)
└── test_llm.py           ✅ MODIFIED
```

---

## Phase 9A.2: Academic KG Improvements

### Status: ✅ COMPLETE (2026-01-27)

### Overview
Knowledge graph optimizations inspired by the Chilean dictatorship KG paper (arXiv:2408.11975). Implements research-backed improvements for document processing, graph quality, and extraction evaluation.

**Implementation Plan:** `docs/plans/2026-01-27-academic-kg-improvements.md`

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 9A.2.1 | `extract/chunker.py` | ✅ | Document text chunking (5000-char, 10% overlap) |
| 9A.2.2 | `extract/llm.py` | ✅ | Chunking integration for long documents |
| 9A.2.3 | `structure/postprocessor.py` | ✅ | Transitive redundancy removal |
| 9A.2.4 | `structure/postprocessor.py` | ✅ | Location hierarchy validation with cycle detection |
| 9A.2.5 | `structure/builder.py` | ✅ | Postprocessor integration |
| 9A.2.6 | `structure/schema.py` | ✅ | LocationNature, OrganizationNature enums |
| 9A.2.7 | `tests/golden/` | ✅ | Golden standard evaluation dataset |

### Implementation Details

**Document Chunking (Chilean KG Paper Optimal Parameters):**
- Chunk size: 5000 characters
- Overlap ratio: 10%
- Sentence boundary detection for clean splits
- Metadata tracking (chunk index, original positions)
- Entity merging across chunks with deduplication

**Graph Post-Processing:**
- Transitive redundancy removal for LOCATED_IN relations
- Self-loop removal
- Dry-run mode for impact analysis
- Location hierarchy validation (detects cycles, hierarchy violations)

**Entity Disambiguation Enums:**
```python
class LocationNature(str, Enum):
    ADMINISTRATIVE = "ADMINISTRATIVE"  # Political/jurisdictional
    GEOGRAPHIC = "GEOGRAPHIC"          # Physical features
    PROPERTY = "PROPERTY"              # Named estates/fincas

class OrganizationNature(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    BUSINESS = "BUSINESS"
    RELIGIOUS = "RELIGIOUS"
    PROFESSIONAL = "PROFESSIONAL"
```

**Golden Standard Evaluation:**
- Sample notarial document (Escritura Publica)
- Expected extraction output with entities/relations
- 7 tests for extraction quality metrics

### Files Created
```
farmer_factory/
├── extract/
│   └── chunker.py              ✅ TextChunker class
└── structure/
    └── postprocessor.py        ✅ GraphPostProcessor class

tests/
├── extract/
│   └── test_chunker.py         ✅ 9 tests
├── structure/
│   └── test_postprocessor.py   ✅ 9 tests
└── golden/
    ├── __init__.py             ✅
    ├── data/
    │   ├── sample_escritura.txt
    │   └── expected_extraction.json
    └── test_golden_evaluation.py  ✅ 7 tests
```

### Test Coverage
- 25 new tests added (all passing)
- Chunker: boundary detection, overlap, reconstruction
- Postprocessor: transitive removal, self-loops, cycle detection, hierarchy validation
- Golden: extraction quality evaluation framework

### Next Steps
- EVENT entity type implementation (see design doc)
- Extraction fine-tuning based on golden test results

---

## Phase 9A.3: OCR Translation & Text Normalization

### Status: ✅ COMPLETE (2026-01-28)

### Overview
Offline translation of non-English OCR text during document processing, with dual-backend support (local CTranslate2 or Google Cloud Translation). Also includes OCR text normalization for cleaner output.

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 9A.3.1 | `extract/translator.py` | ✅ | Dual-backend translation service (local + GCP) |
| 9A.3.2 | `extract/ocr.py` | ✅ | OCR text normalization (newlines, hyphenation) |
| 9A.3.3 | `processing/pipeline.py` | ✅ | Translation step with feature flag |
| 9A.3.4 | `config/settings.py` | ✅ | `translation_enabled`, `translation_backend` settings |
| 9A.3.5 | Frontend integration | ✅ | "English" tab in DocumentViewer when translation exists |
| 9A.3.6 | API route | ✅ | Reads pre-generated translations from `ocr_translated/` |
| 9A.3.7 | Documentation | ✅ | Admin guide setup instructions |

### Architecture

**Two translation backends, same interface:**

| Backend | Setting | How It Works | Trade-offs |
|---------|---------|--------------|------------|
| **Local** (default) | `TRANSLATION_BACKEND=local` | CTranslate2 + subword-nmt with Argos model files | Free, offline, no PII exposure. Lower quality, 30s model load. |
| **GCP** | `TRANSLATION_BACKEND=gcp` | Google Cloud Translation API v2 | Better quality for legal docs. 500k chars/month free, then $20/M. |

**Why not the Argos Python API?**
The `argostranslate` Python package pulls in stanza → PyTorch → OpenMP conflicts → segfaults on macOS. We bypass it entirely and call CTranslate2 (the underlying engine) directly with a pure-Python BPE tokenizer (`subword-nmt`). Same model, same output, no native library conflicts.

### Data Flow
```
Processing Pipeline (TRANSLATION_ENABLED=true)
        ↓
OCR text + detected language
        ↓
needs_translation("es") → True
        ↓
translate_text(ocr_text, source_language="es")
        ↓ (local: CTranslate2 + BPE | gcp: Cloud Translation API)
Translated text saved to cases/CASE-ID/ocr_translated/{doc_id}.txt
        ↓
Frontend reads file → shows "English" tab in DocumentViewer
```

### OCR Text Normalization
- Joins hyphenated line breaks ("Dis-\ntrito" → "Distrito")
- Collapses excessive newlines (3+ → 2)
- Joins mid-sentence line breaks within paragraphs
- Applied during OCR processing, before translation

### Files Created/Modified
```
farmer_factory/extract/
├── translator.py          ✅ NEW - Dual-backend translation service
├── ocr.py                 ✅ MODIFIED - Added normalize_ocr_text()
└── __init__.py            ✅ MODIFIED - Added translator exports

farmer_factory/config/
└── settings.py            ✅ MODIFIED - translation_enabled, translation_backend

farmer_factory/processing/
└── pipeline.py            ✅ MODIFIED - Translation step + KMP_DUPLICATE_LIB_OK

farmer_factory/requirements.txt  ✅ MODIFIED - ctranslate2, subword-nmt

farmer_vault/
├── app/api/cases/[caseId]/document/[docId]/route.ts  ✅ MODIFIED - Reads translations
└── components/Documents/DocumentViewer.tsx            ✅ MODIFIED - English tab

docs/guides/ADMIN_GUIDE.md  ✅ MODIFIED - Translation setup docs
```

### Key Decisions
- **Feature-flagged:** `TRANSLATION_ENABLED=false` by default for compliance
- **Processing-time:** Translations run once during processing, not on-demand
- **Offline-first:** Local backend is default (zero cost, no PII exposure)
- **GCP migration path:** Swap `TRANSLATION_BACKEND=gcp` when quality matters

---

## Phase 9C: Entity Merge Authority

### Status: ✅ COMPLETE (2026-01-29)

### Overview
YAML-based entity merge authority system enabling analyst-driven entity merges on top of automated dedupe. Produces per-type YAML files in `entity_groups/` with two-level status (DRAFT/CONFIRMED) and graph surgery via `apply-merges`.

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 9C.1 | `structure/merge_models.py` | ✅ | Pydantic models: MergeGroup, EntityGroupFile, CrossTypeRelationsFile |
| 9C.2 | `structure/merge_writer.py` | ✅ | Write DRAFT groups from dedupe, preserve CONFIRMED, analyst merge |
| 9C.3 | `structure/merge_reader.py` | ✅ | Read entity groups, get confirmed merges, iterate all files |
| 9C.4 | `structure/merge_engine.py` | ✅ | Graph surgery: node merge, relation rewrite, dedup, metadata recompute |
| 9C.5 | CLI commands | ✅ | `apply-merges` and `merge-entities` commands |
| 9C.6 | Pipeline integration | ✅ | Auto-generate DRAFT merge files + apply confirmed merges |
| 9C.7 | Tests | ✅ | 54 tests across 4 test files |

### Architecture

```
Processing Pipeline
        ↓
Dedupe merges entities automatically (builder.py)
        ↓
Graph exported to graph_data.json
        ↓
DRAFT merge files generated in entity_groups/*.yaml
        ↓
Analyst reviews YAML: DRAFT → CONFIRMED
        ↓
apply-merges rewrites graph (node merge, relation rewrite, metadata recompute)
```

### Files Created
```
farmer_factory/structure/
├── merge_models.py     ✅ Pydantic models (MergeGroup, EntityGroupFile, etc.)
├── merge_writer.py     ✅ Write/update entity group YAML files
├── merge_reader.py     ✅ Read entity groups, get merge maps
└── merge_engine.py     ✅ Graph surgery engine (apply_merges)

tests/structure/
├── test_merge_models.py   ✅ 17 tests
├── test_merge_writer.py   ✅ 9 tests
├── test_merge_reader.py   ✅ 10 tests
└── test_merge_engine.py   ✅ 18 tests
```

### CLI Commands Added
- `apply-merges CASE-ID [--include-drafts]` — Apply confirmed merges to graph_data.json
- `merge-entities CASE-ID ENTITY_A ENTITY_B` — Analyst-driven merge (positional args)
- `rebuild-graph CASE-ID [--skip-validation]` — Rebuild graph from existing extractions (no OCR/LLM)

### Key Design Decisions
- **Two-level status:** File-level + per-entry DRAFT/CONFIRMED
- **Layered merges:** Analyst merges layer on top of dedupe merges (not replace)
- **Idempotent:** Running apply-merges twice produces same result
- **Staleness detection:** `extractions_hash` warns when merge files are stale
- **Metadata recompute:** entity_count, relation_count, verification_distribution updated after merge
- **Rebuild clears stale merges:** `rebuild-graph` deletes old `entity_groups/*.yaml` because entity IDs change on rebuild
- **Conflict provenance:** Entity merges store rejected values in `_merge_conflicts` dict (not as list-valued fields)

---

## Phase 9D: Frontend Document Grouping Integration

### Status: ✅ COMPLETE (2026-01-29)

### Overview
Vault (Next.js frontend) now respects `document_groups.yaml` across all API routes, presenting grouped multi-part documents as single logical entries with multi-page navigation.

### Changes

| Area | File | Change |
|------|------|--------|
| Documents list API | `app/api/cases/[caseId]/documents/route.ts` | Aggregates grouped extraction files into single entries; loads `document_groups.yaml` |
| Single document API | `app/api/cases/[caseId]/document/[docId]/route.ts` | `handleGroupedDocument()` merges all pages' entities, OCR, translations; returns `pages[]` array |
| Image API | `app/api/cases/[caseId]/document/[docId]/image/route.ts` | `?page=N` query param for serving specific group file images |
| Timeline API | `app/api/cases/[caseId]/timeline/route.ts` | Groups extraction files by document group; deduplicates timeline entries |
| Document viewer | `components/Documents/DocumentViewer.tsx` | Multi-page navigation (prev/next); per-page OCR, translation, entities; iframe PDF viewer |
| Document list | `components/Documents/DocumentList.tsx` | Date sort order toggle (ascending/descending) |
| Dependencies | `package.json` | Added `js-yaml` + `@types/js-yaml` |

### Frontend API Changes
- Grouped documents use `doc_<group_id>` as their document ID
- Single document API returns `pages[]` array for grouped docs (each page has `ocrText`, `translatedText`, `imagePath`, `entities`)
- Image API accepts `?page=N` to serve specific pages within a group
- `inferType()` expanded: Property, Survey, Financial, Inheritance types added

### Key Design Decisions
- **Backward compatible:** No `document_groups.yaml` = all documents treated as standalone (existing behavior)
- **Only CONFIRMED groups:** DRAFT groups are ignored by frontend
- **Aggregate stats:** Entity counts, confidence scores aggregated across all pages in a group
- **Page-level content:** OCR text, translations, and entities are per-page, not concatenated
- **Iframe viewer:** Replaced manual zoom controls with native browser PDF rendering via `<iframe>`

---

## Phase 9B: Document Grouping

### Status: ✅ COMPLETE (2026-01-27)

### Overview
Multi-part document handling for cases where a single logical document is split across multiple PDF files (e.g., `escritura_125_1.pdf`, `escritura_125_2.pdf`).

### Workflow
```
1. Analyst adds PDFs to intake/
2. CLI auto-detects groupings: detect-groups CASE-ID
3. Analyst reviews document_groups.yaml (DRAFT)
4. Analyst confirms: status: CONFIRMED
5. Process creates unified DOCUMENT entities per group
```

### Tasks

| Task | File | Status | Notes |
|------|------|--------|-------|
| 9B.1 | `intake/document_groups.py` | ✅ | Pattern detection, YAML generation |
| 9B.2 | `cli.py detect-groups` | ✅ | CLI command with reporting |
| 9B.3 | `cli.py process` | ✅ | DRAFT status blocking |
| 9B.4 | `structure/builder.py` | ✅ | Unified DOCUMENT entities |
| 9B.5 | Tests | ✅ | 21 tests for grouping logic |

### Detection Patterns
- `foo_1.pdf, foo_2.pdf` (numbered suffix)
- `foo_a.pdf, foo_b.pdf` (letter suffix)
- `foo (1).pdf, foo (2).pdf` (parenthesis)
- `foo-1.pdf, foo-2.pdf` (hyphen)
- `fooP1.pdf, fooP2.pdf` (page indicator)

### Safety Rails
- `process` refuses if `document_groups.yaml` is DRAFT
- Validation catches missing/unaccounted files
- Backward compatible (no YAML = all standalone)

### Files Created
```
farmer_factory/intake/document_groups.py   # Core logic
tests/intake/test_document_groups.py       # 21 tests
```

---

## Success Criteria

### MVP1 Complete When:
- ✅ 300 documents processed via CLI
- ✅ graph_data.json validates against schema
- ✅ **Case creation via CLI works** (create-case command)
- ✅ **Graph uploaded to Supabase Storage** (upload command)
- ✅ **Authentication works** (Clerk OAuth + MFA)
- ✅ **Database RLS enforces case isolation** (tested with 2+ users)
- ✅ **Frontend fetches graph from Supabase** (not local file)
- ✅ Frontend renders graph (requires login)
- ✅ **Analyst can verify entities** (TIER_3_AI → TIER_2_ANALYST)
- ✅ **Verification updates graph in real-time**
- ✅ Dossier panel works
- ✅ All verification tiers display correctly
- ✅ Legal disclaimer present and prominent
- ✅ Audit trail captured (all access logged)
- ✅ **Deployed to Vercel with HTTPS**
- ✅ **Security headers configured**
- ✅ Can invite family members to view case
- ✅ **ADMIN_GUIDE.md operational procedures followed**
- ✅ **ANALYST_GUIDE.md verification procedures followed**
- ✅ **Forensic Dossier PDF export works** (generate-dossier command)
- ✅ **Dossier includes all 7 sections** (front matter, timeline, family, property, ownership, evidence, appendix)
- ✅ **Executive summary is LLM-polished** (hybrid template + Claude)
- ✅ **PDF downloadable from Vault** (authenticated endpoint)
- 🔲 **Property geolocation maps** (optional enhancement, Phase 8A.3)

### Strategic Foundation Complete When:
- ✅ **Civic Architecture Vision documented** (`docs/strategy/CIVIC_ARCHITECTURE_VISION.md`)
- ✅ **Market analysis completed** (genealogy, academic, journalism, parallel restitution)
- ✅ **Competitive landscape documented** (gap identified, no direct competitor)
- ✅ **Domain configuration schema designed** (Phase 9 planned)
- 🔲 **Methodology publication outlined** (general, not Cuba-specific)
- 🔲 **Domain #2 partner identified** (genealogy society, academic project, or parallel restitution)

---

*Reference other docs: ARCHITECTURE.md, SCHEMA.md, PROMPTS.md, PREPROCESSING.md, FRONTEND.md*
