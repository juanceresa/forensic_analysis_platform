# CLAUDE.md — Instructions for Claude Code

> **Version:** 2.6.0
> **Last Updated:** 2026-01-27
> **Status:** Master instructions file (Academic KG improvements complete)

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
- OCR, AI inference, entity extraction
- Clients NEVER see this zone

**Zone B (The Vault)** — Next.js frontend
- Read-only static rendering
- Clients can ONLY view, never upload/edit/delete
- Consumes `graph_data.json` from Zone A

**See:** `docs/architecture/ARCHITECTURE.md` for complete system design.

### 2. Legal Posture

We produce **Forensic Facts**, never **Legal Strategy**.

**ALLOWED:**
- "Document X states Y owned Z in 1958"
- "OCR confidence is 72%"
- "Three documents corroborate this claim"

**FORBIDDEN:**
- "This proves ownership"
- "You have a strong case"
- "This is legally valid"

**See:** `docs/architecture/POSTURING.md` for organizational strategy.

### 3. The Verification Tiers

Every data point MUST have a `verification` field with 4-tier system (TIER_3_AI → TIER_1_CERTIFIED).

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

### Operational Guides
- **`docs/guides/`**
  - `ADMIN_GUIDE.md` - System administration
  - `ANALYST_GUIDE.md` - Verification workflow

### Module Documentation
- **`farmer_factory/intake/`**
  - `document_groups.py` - Multi-part document grouping (auto-detect + analyst review)

- **`farmer_factory/extract/`**
  - `README.md` - Module overview
  - `PROMPTS.md` - LLM extraction prompts
  - `chunker.py` - Document text chunking (5000-char chunks, 10% overlap)

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
- Never let LLM make legal conclusions

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

### Process documents
```bash
python -m farmer_factory.cli process CASE-ID --domain cuban_property --force-typed
```

### Train entity deduplication
```bash
python -m farmer_factory.cli train-deduplication CASE-ID --domain cuban_property --entity-type PERSON
```

### Clean case for re-processing
```bash
python -m farmer_factory.cli clean CASE-ID --confirm
```

### List entities in a case
```bash
python -m farmer_factory.cli list-entities CASE-ID [--type PERSON|PROPERTY|ORGANIZATION|LOCATION|DOCUMENT]
```

### Generate forensic dossier PDF
```bash
python -m farmer_factory.cli generate-dossier CASE-ID --property-id X --family-member-id Y --domain cuban_property [--dry-run]
```

**Note:** The `--domain` flag defaults to `cuban_property` if not specified.

---

## Current Phase

**See:** `.claude/ROADMAP.md` for current implementation status.

**Recent:** Phase 9A - Academic KG Improvements (✅ COMPLETE - 2026-01-27)
**Status:** Chilean KG paper optimizations implemented — chunking, post-processing, golden tests

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
- Phase 9B - Document Grouping (✅ COMPLETE - 2026-01-27)
  - Auto-detect multi-part documents from filename patterns
  - Analyst review workflow (DRAFT → CONFIRMED)
  - Unified DOCUMENT entities for grouped files
  - CLI: `detect-groups` command

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

1. **Never** make legal conclusions in prompts or output
2. **Never** allow Zone B to modify data
3. **Never** display TIER_3_AI data without disclaimer
4. **Never** skip the verification field on any node/link
5. **Never** expose raw AI inference to clients without context

---

*For detailed documentation, see the files referenced above. This is your navigation guide to the codebase.*
