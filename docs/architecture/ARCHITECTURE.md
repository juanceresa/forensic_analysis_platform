# Farmer House Forensic Intelligence Platform — Architecture Document

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.1.0
> **Last Updated:** 2026-01-21
> **Status:** PLANNING PHASE — MVP1 (with OCR baseline established)

---

## Executive Summary

The Farmer House Forensic Intelligence Platform is a **Civic Intelligence Bureau** for historical property restitution. It digitizes, verifies, and maps contested pre-revolutionary property claims (initially Cuban exile land deeds from the Ceresa Family Archive).

This is **not a SaaS product**. It is a **Service Bureau** model: we process data internally; clients only view static results.

---

## The "Air Gap" Architecture

The system is strictly divided into two zones to manage liability:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ZONE A: THE FACTORY                         │
│                    (Internal Python Processing)                     │
│                                                                     │
│  • Raw document scanning and OCR                                    │
│  • "Messy" AI inference and entity extraction                       │
│  • Human analyst verification workflows (TIER_3_AI → TIER_2_ANALYST)│
│  • All processing happens here — clients never see this             │
│                                                                     │
│  Tech: Python 3.10+, NetworkX, Google Cloud Vision, Anthropic API   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ CLI upload command
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SUPABASE (Data Layer)                           │
│                                                                     │
│  • Storage: case-graphs bucket (graph_data.json per case)          │
│  • Database: cases, users, case_access, audit_logs                 │
│  • RLS: Case isolation enforced at database level                  │
│                                                                     │
│  Tech: PostgreSQL with Row-Level Security, Storage with auth       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ API fetch with RLS check
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ZONE B: THE VAULT                           │
│                  (Client-Facing Next.js Read-Only)                  │
│                                                                     │
│  • Digital dossier — READ ONLY (families cannot upload/edit/delete)│
│  • Analysts CAN verify (promote TIER_3_AI → TIER_2_ANALYST)        │
│  • Intelligence-grade evidence map aesthetic                        │
│                                                                     │
│  Tech: Next.js 14 (App Router), Tailwind CSS, react-force-graph-2d  │
└─────────────────────────────────────────────────────────────────────┘
```

### Why the Air Gap Matters

1. **Liability Isolation**: Client never touches raw data or unverified AI inference
2. **Legal Clarity**: We produce Forensic Facts, not Legal Strategy
3. **Audit Trail**: All processing is logged in Zone A; Zone B is immutable output
4. **Trust Model**: Clients consume curated, verified output — not the sausage factory

---

## Legal Posture: The "Home Inspector" Model

### What We Are
- **Forensic Fact Finders** — we verify what documents say
- **Independent Standard** — not captured by any law firm
- **Pre-Litigation Intelligence** — families use our dossier to negotiate with lawyers

### What We Are NOT
- **Legal Advisors** — we do not provide legal strategy
- **Advocates** — we do not argue for or against claims
- **Restitution Agents** — we do not promise outcomes

### The UPL (Unauthorized Practice of Law) Shield

| Permitted | Prohibited |
|-----------|------------|
| "This document states Mario Ceresa owned the mill in 1958" | "This document means you will win $2 million" |
| "The OCR confidence on this signature is 72%" | "This signature is legally valid" |
| "These three documents corroborate ownership" | "You have a strong legal case" |

**Every output must be a Forensic Fact, never a Legal Conclusion.**

---

## The Verification Tiers

This is the core value proposition. Every data point (node or link) carries a `verification_status`:

| Tier | Label | Provider | Color | Meaning | Display Rule |
|------|-------|----------|-------|---------|--------------|
| `TIER_3_AI` | AI Extracted | Civic Table platform | Grey | LLM-extracted, automated | **Must display disclaimer** |
| `TIER_2_ANALYST` | Analyst Verified | Civic Table analyst | Gold | Human analyst confirmed | Verified badge |
| `TIER_2_INSTITUTIONAL` | Farmer House Verified | Farmer House analyst | Gold + "FH" badge | Institutional validation | Institutional badge |
| `TIER_1_CERTIFIED` | Legally Certified | External legal body | Blue | Notarized/Legal Truth | Certification badge |

### Tier Promotion Rules

```
TIER_3_AI ──[Civic Table analyst]──> TIER_2_ANALYST
          └──[Farmer House analyst]──> TIER_2_INSTITUTIONAL
                                              └──[legal certification]──> TIER_1_CERTIFIED
```

- **TIER_3 → TIER_2_ANALYST**: Civic Table analyst reviews against source documents
- **TIER_3 → TIER_2_INSTITUTIONAL**: Farmer House analyst independently verifies (optional premium)
- **TIER_2 → TIER_1**: External legal certification (e.g., FCSC, notarization)
- **Demotion**: Not permitted — once verified, a fact stays verified (but can be flagged as "superseded")

### Strategic Importance

**TIER_2_ANALYST is Civic Table's core business:**
- Always available (no external dependency)
- Sufficient for most family use cases
- Civic Table owns the verification process

**TIER_2_INSTITUTIONAL is optional premium:**
- Requires partnership with Farmer House
- Higher credibility for legal proceedings
- Can be removed if partnership ends without affecting core business

**TIER_1_CERTIFIED is external:**
- Legal certification from third parties
- Outside Civic Table's control
- Highest legal weight

### MVP1 Scope Note

In MVP1:
- All extracted data starts as `TIER_3_AI` (automated)
- **`TIER_2_ANALYST` verification workflow INCLUDED** (analyst UI for promoting entities)
- `TIER_2_INSTITUTIONAL` designed but partnership not yet active
- `TIER_1_CERTIFIED` is external process (not implemented in platform)

**MVP1 Analyst Workflow:**
1. Factory processes documents → all entities start as TIER_3_AI
2. Analyst reviews entities in Vault UI
3. Analyst promotes verified entities → TIER_2_ANALYST
4. Graph updates in real-time
5. Families see mix of TIER_3_AI (unverified) and TIER_2_ANALYST (verified)

---

## Data Flow Architecture

```
                    ┌─────────────────┐
                    │   PDF INTAKE    │
                    │ (300 documents) │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PRE-PROCESSING                              │
│                                                                     │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│   │  Deskew  │──▶│ Contrast │──▶│ Binarize │──▶│ Segment  │        │
│   └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│                                                                     │
│   • Align rotated scans           • Separate handwritten regions   │
│   • Enhance faded ink             • Detect stamps, signatures      │
│   • Clean for OCR                 • Route regions to OCR models    │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DOCUMENT TRIAGE                               │
│                                                                     │
│   ┌──────────────┐                      ┌──────────────┐           │
│   │  OCR Quality │──[High]──▶ Standard  │   OCR Path   │           │
│   │  Assessment  │            Pipeline  └──────────────┘           │
│   └──────────────┘                                                 │
│         │                                                           │
│         └──[Low]──▶ Manual Transcription Queue                     │
│                     (Handwritten/degraded documents)               │
│                                                                     │
│   Reality Check (Ceresa Archive):                                  │
│   • 80 documents tested                                            │
│   • 27 highly usable via OCR (~34%)                                │
│   • 53 require manual transcription or vision model interpretation │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            OCR                                      │
│                                                                     │
│   ┌─────────────────────┐   ┌─────────────────────┐                │
│   │  Google Cloud Vision │   │ Claude Vision API   │                │
│   │  (Typed Text)        │   │ (Handwriting)       │                │
│   └─────────────────────┘   └─────────────────────┘                │
│                                                                     │
│   • Spanish language primary                                        │
│   • Per-region confidence scores                                    │
│   • Low-confidence (<60%) regions flagged for manual review        │
│   • Handwritten documents may use vision model interpretation      │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       POST-PROCESSING                               │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│   │ LLM OCR     │──▶│ Entity       │──▶│ Relation     │           │
│   │ Cleanup     │   │ Extraction   │   │ Extraction   │           │
│   │ (Haiku)     │   │ (Haiku)      │   │ (Haiku)      │           │
│   └──────────────┘   └──────────────┘   └──────────────┘           │
│          │                                     │                    │
│          ▼                                     ▼                    │
│   ┌──────────────┐                      ┌──────────────┐           │
│   │ Coreference  │                      │ Schema       │           │
│   │ Resolution   │                      │ Validation   │           │
│   └──────────────┘                      └──────────────┘           │
│                                                                     │
│   • "Don Mario" = "M. Ceresa" = "Mario Ceresa"                     │
│   • PERSON -[OWNS]-> PROPERTY                                       │
│   • DOCUMENT -[CONFISCATES]-> PROPERTY                             │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      GRAPH CONSTRUCTION                             │
│                                                                     │
│   • NetworkX graph from entities and relations                     │
│   • Deduplication and entity resolution                            │
│   • Gap detection (missing links in ownership chains)              │
│   • Confidence scoring at node and link level                      │
│                                                                     │
│   Output: graph_data.json (local file)                             │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SUPABASE STORAGE UPLOAD                           │
│                                                                     │
│   • CLI command: python -m farmer_factory.cli upload CASE-001      │
│     (Note: upload command is planned but not yet implemented)       │
│   • Uploads graph_data.json to Supabase Storage bucket             │
│   • Path: case-graphs/CASE-001/graph_data.json                     │
│   • RLS ensures only authorized users can access                   │
│                                                                     │
│   Admin also creates case record in database for access control    │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      VAULT RENDERING                                │
│                                                                     │
│   • API route fetches graph from Supabase Storage (with RLS check) │
│   • Force-directed graph (evidence map style)                      │
│   • Node colors by verification tier                               │
│   • Right-side dossier panel on click                              │
│   • Analyst review panel (promote to TIER_2_ANALYST)               │
│   • Source document viewer with OCR overlay                        │
│                                                                     │
│   Families: READ-ONLY | Analysts: Can verify entities              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Zone A: The Factory (Python)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.10+ | Data science ecosystem, LangChain compatibility |
| Graph Logic | NetworkX | Mature, well-documented, good for analysis |
| OCR (Typed) | Google Cloud Vision | Best-in-class for degraded historical documents |
| OCR (Handwritten) | Google Cloud Vision Handwriting API | Better than Tesseract for cursive |
| LLM | Anthropic Claude API | Entity/relation extraction with structured output |
| Schema Validation | Pydantic | Type safety, JSON serialization |
| Image Processing | OpenCV, Pillow | Preprocessing pipeline |
| PDF Handling | PyMuPDF (fitz) | Fast PDF parsing and image extraction |

### Zone B: The Vault (Next.js)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Framework | Next.js 16 (App Router) | Static export, modern React |
| Styling | Tailwind CSS + shadcn/ui | Radix primitives, dark mode |
| Graph Visualization | react-force-graph-2d | Force-directed physics-based layout |
| State Management | None (static data) | Read-only, no client state needed |
| Auth (interim) | Cookie-based password gate | Simple shared password for family sharing |
| Deployment (MVP1) | Local + cloudflared tunnel | No Vercel/Supabase until MVP2 |

### Database (MVP2+)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Primary DB | PostgreSQL (Supabase) | Relational + JSON support |
| Vector Search | pgvector | Semantic search without separate service |

---

## Handwritten Document Processing Strategy

Based on Ceresa Archive testing (80 documents, 34% OCR success rate), handwritten documents require specialized handling:

### Three-Tier Approach

**Tier 1: OCR Attempt (All Documents)**
- Run Google Cloud Vision with Spanish language model
- Collect confidence scores per word/region
- Flag entire document if avg confidence <60%

**Tier 2: Vision Model Interpretation (Low OCR Confidence)**
- Route flagged documents to Claude Vision API
- Provide high-res document image + prompt for structured extraction
- Vision model reads handwriting directly, bypasses OCR
- Extract entities/relations in single pass
- Cost: ~$0.003 per page (acceptable for 200-page subset)

**Tier 3: Manual Transcription Queue (Critical Documents)**
- Documents with historical/legal significance but poor automated extraction
- Human transcriber creates clean text version
- Re-run through standard entity extraction pipeline
- Criteria: Property ownership docs, confiscation decrees, legal filings

### Vision Model Prompt Template

```
You are analyzing a historical handwritten document from pre-revolutionary Cuba (1950s).

<image>
[Document scan]
</image>

Extract the following in JSON format:
- Document type (deed, certificate, correspondence, etc.)
- Date (if visible)
- All person names mentioned
- All property names/locations mentioned
- Key transactions or legal actions described
- Confidence score (0.0-1.0) for your extraction

Preserve original Spanish text. Note areas that are illegible.
```

### Workflow Decision Tree

```
Document → OCR → Confidence Check
                      │
                      ├─ >70% confidence → Standard pipeline
                      │
                      ├─ 40-70% confidence → Vision model interpretation
                      │
                      └─ <40% confidence → Manual transcription queue
                                            (if document is flagged as critical)
```

### Expected Throughput

| Path | Documents | Time/Doc | Total Time |
|------|-----------|----------|------------|
| Standard OCR | ~100 (34%) | 2 min | 3.3 hours |
| Vision model | ~150 (50%) | 5 min | 12.5 hours |
| Manual transcription | ~50 (16%) | 30 min | 25 hours |
| **Total** | **300** | — | **~41 hours** |

*Note: Times include preprocessing, extraction, and review steps.*

---

## API Cost Estimates (MVP1)

Based on 300 documents averaging 3 pages each (900 pages total):

| Service | Usage | Unit Cost | Est. Total |
|---------|-------|-----------|------------|
| **Google Cloud Vision** | 900 pages OCR | $1.50 / 1K pages | $1.35 |
| **Claude API (Entity)** | 300 docs × 2K tokens avg | $3 / 1M tokens (Haiku) | $1.80 |
| **Claude API (Relations)** | 300 docs × 1.5K tokens avg | $3 / 1M tokens | $1.35 |
| **Claude API (Summary)** | 300 docs × 1K tokens avg | $3 / 1M tokens | $0.90 |
| **Claude Vision (Handwritten)** | ~200 pages (fallback) | $3 / 1M tokens (~1K/page) | $0.60 |
| | | **MVP1 Total** | **~$6.00** |

**Retry Budget:**
- Low-confidence retries (est. 15%): +$1.50
- **Total with retries: ~$7.50**

**Production Scaling (1,000 documents):**
- Base processing: ~$20
- Quality review passes: +$10
- **Est. total: ~$30 per 1,000 documents**

**Cost Optimization Notes:**
- Use Claude Haiku for initial extraction (10× cheaper than Sonnet)
- Use Sonnet only for low-confidence retries or complex documents
- Batch API requests where possible
- Cache OCR results to avoid re-processing

---

## Error Budget & Acceptance Criteria

### OCR Quality Thresholds

| Document Type | Min Confidence | Action if Below |
|---------------|----------------|-----------------|
| Typed (clean) | 85% | Retry with enhanced preprocessing |
| Typed (faded) | 70% | Manual review recommended |
| Handwritten (structured) | 60% | Route to vision model interpretation |
| Handwritten (cursive) | 50% | Manual transcription queue |

**Overall Target:** 70% of documents achieve >60% OCR confidence

### Entity Extraction Targets

| Metric | MVP1 Target | Production Target |
|--------|-------------|-------------------|
| Entity Precision | ≥75% | ≥85% |
| Entity Recall | ≥65% | ≥80% |
| Relation Precision | ≥70% | ≥80% |
| Relation Recall | ≥60% | ≥75% |
| Coreference F1 | ≥70% | ≥85% |

**Measurement:** Compare against 20-document golden dataset (manually annotated)

### Processing Failure Limits

| Stage | Max Failure Rate | Response |
|-------|------------------|----------|
| PDF Extraction | 1% | Halt batch, investigate |
| Preprocessing | 5% | Continue, flag for review |
| OCR | 30% (expected) | Route to manual queue |
| Entity Extraction | 10% | Retry with higher-quality model |
| Graph Construction | 2% | Review schema validation |

### Temporal Resolution

| Precision Level | Acceptable Variance | Example |
|----------------|---------------------|---------|
| Exact date | ±0 days | "March 15, 1958" |
| Month | ±15 days | "March 1958" → March 1-31 |
| Year | ±6 months | "1958" → Jan-Dec 1958 |
| Decade | ±2 years | "1950s" → 1948-1962 |
| Unknown | Not used in timeline | Flagged for research |

**Conflict Resolution:** When multiple sources give different dates:
1. Certified documents (TIER_1) override all others
2. Notarized documents (TIER_2) override unverified
3. Earlier creation date takes precedence (deed date > later correspondence)
4. If uncertainty remains, store both with conflict flag

### Graph Complexity Limits

| Metric | MVP1 Warning | MVP1 Max |
|--------|--------------|----------|
| Total nodes | 1,000 | 2,000 |
| Total links | 2,500 | 5,000 |
| Nodes per entity type | 500 | 1,000 |
| Orphan nodes (no connections) | <5% | <10% |
| Average node degree | 3-8 | 2-15 |

**If limits exceeded:** Implement entity clustering or filtered views

---

## Directory Structure

### Zone A: farmer_factory/

```
farmer_factory/
├── intake/
│   ├── __init__.py
│   ├── pdf_loader.py          # Load PDFs, extract page images
│   ├── provenance.py          # Chain of custody tracking
│   └── manifest.py            # Document inventory management
├── prepare/
│   ├── __init__.py
│   ├── deskew.py              # Image alignment correction
│   ├── enhance.py             # Contrast, histogram equalization
│   ├── binarize.py            # Otsu/Sauvola binarization
│   ├── segment.py             # Region detection (text, stamp, signature)
│   └── pipeline.py            # Orchestrate preprocessing
├── extract/
│   ├── __init__.py
│   ├── ocr_engine.py          # Google Cloud Vision integration
│   ├── ocr_postprocess.py     # Error correction, normalization
│   ├── entity_extractor.py    # NER + LLM extraction
│   ├── relation_extractor.py  # Link entities into relations
│   └── confidence_scorer.py   # Assign TIER_3 confidence scores
├── structure/
│   ├── __init__.py
│   ├── graph_builder.py       # NetworkX graph construction
│   ├── deduplicator.py        # Entity resolution / coreference
│   ├── gap_detector.py        # Find missing links in chains
│   └── schema.py              # Pydantic models for all types
├── export/
│   ├── __init__.py
│   ├── json_exporter.py       # graph_data.json for frontend
│   ├── pdf_generator.py       # Dossier PDF with citations (MVP2)
│   └── audit_log.py           # Full processing trace
├── config/
│   ├── prompts/               # LLM prompts for extraction
│   │   ├── entity_prompt.txt
│   │   └── relation_prompt.txt
│   ├── taxonomies/            # Entity/relation type definitions
│   │   └── types.yaml
│   └── settings.py            # API keys, paths, thresholds
├── cli.py                     # Command-line interface
├── main.py                    # Pipeline orchestration
└── requirements.txt
```

### Zone B: farmer_vault/

```
farmer_vault/
├── middleware.ts               # Password auth gate (interim, pre-Clerk)
├── app/
│   ├── layout.tsx             # Dark theme, monospace fonts
│   ├── page.tsx               # Dashboard entry
│   ├── globals.css            # Tailwind + custom styles
│   ├── login/page.tsx         # Password login page
│   ├── api/
│   │   ├── auth/login/route.ts # Password auth endpoint
│   │   └── cases/[caseId]/   # Case data API routes
│   │       ├── dashboard/     # Aggregated metrics
│   │       ├── documents/     # Document list (grouped)
│   │       ├── document/[docId]/ # Document detail + image
│   │       ├── entities/      # Entities grouped by type
│   │       ├── entity/[entityId]/ # Entity detail + descriptions
│   │       ├── timeline/      # Timeline periods + narrative
│   │       ├── graph/         # Full graph data
│   │       ├── narrative/     # AI narrative generation
│   │       └── dossier/       # PDF dossier download
│   └── case/[caseId]/
│       ├── page.tsx           # Dashboard
│       ├── documents/         # Document browser
│       ├── entities/          # Entity browser + key events
│       ├── narrative/         # AI Analysis (scroll + sub-routes)
│       └── graph/             # Redirect to /narrative/graph
├── components/
│   ├── Dashboard/             # Dashboard header, dossier download
│   ├── Documents/             # DocumentViewer (raw/cleaned toggle), DocumentList
│   ├── Entities/              # EntityBrowser (+ events), EntityDetail (+ descriptions)
│   ├── Graph/                 # KnowledgeGraph, GraphView (inline settings), EntitySidebar
│   ├── Timeline/              # Scroll experience (Hero, ScrollTimeline, StickySpine, etc.)
│   ├── Narrative/             # TimelinePeriod
│   ├── ui/                    # shadcn/ui primitives
│   └── shared/                # Sidebar, ErrorBoundary, VerificationBadge, etc.
├── lib/
│   ├── types.ts               # TypeScript types matching JSON schema
│   ├── document-groups.ts     # YAML loading, file-to-group mapping
│   ├── document-types.ts      # Document type definitions
│   ├── graph-settings.ts      # Graph display settings
│   └── graph-utils.ts         # Graph data utilities
├── hooks/
│   └── useGraphSettings.ts    # Graph settings hook
├── tailwind.config.js
├── next.config.js
└── package.json
```

---

## Security and Privacy

### Document Handling

- All source PDFs stored locally (no cloud in MVP1)
- Chain of custody logged for every document
- Original scans never modified — all processing creates derivatives

### Redaction Protocol (MVP2)

- Living persons' names: configurable redaction
- Exact addresses: redacted in public artifacts
- Financial amounts: optional redaction
- Analyst-flagged content: always redacted

### Access Control (MVP1)

- **Zone A (Factory)**: Internal only, no external access, VPN required
- **Zone B (Vault)**: OAuth 2.0 authentication via Clerk (required)
- **Database**: Row-Level Security in Supabase (case isolation enforced)
- **MFA**: Required for all case admins and analysts
- **No cross-case data leakage**: Database-level enforcement

**Authentication Provider:** Clerk
- Free tier: 10,000 monthly active users
- MFA included: TOTP, SMS, backup codes
- Session management: Automatic, secure
- Social logins: Google, Apple (optional)

---

## Audit and Compliance

### Audit Log Schema

Every processing step is logged:

```json
{
  "timestamp": "2025-01-21T14:30:00Z",
  "action": "ENTITY_EXTRACTION",
  "input_hash": "sha256:abc123...",
  "output_hash": "sha256:def456...",
  "operator": "ai:claude-3-sonnet",
  "parameters": {
    "prompt_version": "1.0.0",
    "confidence_threshold": 0.7
  },
  "result": {
    "entities_extracted": 5,
    "relations_extracted": 3
  }
}
```

### Audit Trail Storage (MVP1)

**Structure:**
```
cases/
└── CASE-ID/
    ├── intake/                         # Original uploaded documents
    ├── preprocessed/                   # Preprocessed images for OCR
    ├── ocr/                            # Raw OCR text output
    ├── ocr_cleaned/                    # LLM-cleaned OCR text
    ├── ocr_translated/                 # Translated OCR text
    ├── extractions/                    # LLM entity extractions (includes cleaned_text)
    ├── entity_groups/                  # Entity merge authority YAML files
    ├── output/
    │   ├── graph_data.json             # Knowledge graph
    │   ├── case_narrative.json         # Period-based case narrative
    │   ├── entity_descriptions.json    # Per-entity AI descriptions
    │   └── *_dossier.pdf               # Generated dossiers
    ├── metadata.json                   # Case metadata
    ├── manifest.json                   # Processing manifest
    ├── document_groups.yaml            # Multi-part document grouping
    └── processing.log                  # Processing logs
```

**Format:** JSON Lines (.jsonl) for master audit (one JSON object per line, append-only)

**Retention:**
- All audit logs: Permanent (legal discovery requirement)
- Preprocessed images: 90 days (reproducibility window)
- Raw OCR outputs: 30 days (debug only)

### Tamper Evidence (MVP2)

- Hash chain linking all audit entries
- Immutable once written
- Supports legal discovery requirements
- Cryptographic signatures on completed cases

---

## MVP1 Scope Boundaries

### In Scope

- [x] PDF intake from local folder
- [x] Full preprocessing pipeline (deskew, enhance, binarize, segment)
- [x] OCR via Google Cloud Vision
- [x] Entity and relation extraction via Anthropic Claude
- [x] NetworkX graph construction
- [x] JSON export for frontend
- [x] Next.js frontend with force-directed graph
- [x] Dossier panel with source viewer
- [x] CLI interface for pipeline execution

### Out of Scope (MVP2+)

- [ ] Human verification workflow
- [ ] Tier promotion (all data is TIER_3_AI in MVP1)
- [ ] PDF dossier generation
- [ ] Multi-case support (single family for MVP1)
- [ ] Redaction engine

### Added to MVP1 Scope (Security-First Approach)

- [x] **Authentication**: Clerk OAuth 2.0 with MFA
- [x] **Database**: Supabase with Row-Level Security
- [x] **Deployment**: Vercel with HTTPS/TLS
- [x] **Access Control**: Case isolation, role-based permissions
- [x] **Audit Logging**: Complete activity tracking

---

## References

- Working_Scope.docx — Pilot deliverables and posture
- Internal_Governance.docx — Safeguards and scope boundaries
- Testimonial.docx — Founding case rationale
- Document_Recovery_Pilot.docx — Full pilot specification

---

*This document is the authoritative architecture reference for the Farmer House Forensic Intelligence Platform. All implementation decisions should align with the principles and constraints documented here.*
