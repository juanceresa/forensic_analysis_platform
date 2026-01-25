# Farmer House Forensic Intelligence Platform — Implementation Roadmap

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.2.1
> **Last Updated:** 2026-01-24
> **Status:** MVP1 Planning (with dependencies and acceptance criteria)

---

## Overview

This document provides the implementation roadmap for MVP1. It breaks down work into phases and tasks suitable for Claude Code execution.

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
- PDF dossier generation
- Multi-case support (single family for MVP1)
- Case management web UI (CLI-based for MVP1)

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

## Phase 6: Export & CLI

### Dependencies
- **Blocks:** Phase 7 (Frontend needs graph_data.json)
- **Prerequisite:** Phase 5 complete (graph constructed)

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

## Phase 7: Frontend + Authentication

### Dependencies
- **Blocks:** Phase 8 (Integration testing needs UI)
- **Prerequisite:** Phase 6 complete (graph_data.json available)

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

## Phase 8: Integration Testing

### Dependencies
- **Prerequisite:** All phases 1-7 complete

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
│   └── summarizer.py         [ ]
├── structure/
│   ├── schema.py             [✓] # Complete
│   ├── graph_builder.py      [✓] # Complete
│   ├── resolver.py           [ ] # NEW - Dedupe-based entity resolution
│   ├── models/               [ ] # NEW - Trained dedupe models (*.pkl)
│   └── ~~gap_detector.py~~   [x] # DEFERRED to analyst workflow
├── export/
│   ├── json_exporter.py      [ ]
│   └── audit_log.py          [ ]
└── utils/                    [ ] # NEW
    ├── retry.py              [ ] # NEW - Retry with backoff
    ├── cost_tracker.py       [ ] # NEW - API cost logging
    └── supabase_uploader.py  [ ] # NEW - Upload to Supabase Storage
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
│   │           └── verify-entity/route.ts [ ] # NEW - Analyst verification
│   └── case/[id]/page.tsx    [ ]
├── components/
│   ├── KnowledgeGraph.tsx    [ ]
│   ├── DossierPanel.tsx      [ ]
│   ├── NodeBadge.tsx         [ ]
│   ├── SourceViewer.tsx      [ ]
│   ├── TimelineView.tsx      [ ]
│   ├── GapAlert.tsx          [ ]
│   └── AnalystReviewPanel.tsx [ ] # NEW - Analyst verification UI
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

## Success Criteria

MVP1 complete when:
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

---

*Reference other docs: ARCHITECTURE.md, SCHEMA.md, PROMPTS.md, PREPROCESSING.md, FRONTEND.md*
