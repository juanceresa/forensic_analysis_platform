# Civic Table — Forensic Document Intelligence Platform

A full-stack platform for recovering structured ownership records from degraded historical archives. Built to make illegible documents legible to power structures — enabling dispossessed families, researchers, and legal teams to build evidentiary records from deteriorated source material.

**Founding case:** Cuban property restitution from 1950s land deeds. Designed to generalize to genealogy, Holocaust/WWII restitution, Indigenous land claims, and investigative journalism.

Developed at the [Farmer House Democratic Repair Lab](https://www.htu.edu/) at Huston-Tillotson University.

## Architecture

The platform enforces an **air-gapped two-zone architecture**:

| Zone | Stack | Purpose |
|------|-------|---------|
| **Factory** (processing) | Python, Pydantic, NetworkX | OCR, LLM extraction, graph construction, narrative generation |
| **Vault** (client access) | Next.js, TypeScript, Tailwind | Read-only viewing — clients can view, never modify |

Data flows one direction: Factory → Vault. The Vault never writes back.

## Processing Pipeline

Documents pass through a 6-stage pipeline:

```
OCR (Google Cloud Vision)
 → LLM Text Cleanup (Claude Haiku)
   → Entity Extraction (Claude Haiku, 5 entity types)
     → Relation Extraction (Claude Haiku, 28 relation types)
       → Knowledge Graph Construction (NetworkX MultiDiGraph)
         → AI Narrative Generation (Claude Sonnet)
```

Each stage is independently retriable. Failed extractions can be reprocessed without re-running OCR.

## Entity Resolution

The platform implements a **3-layer entity merge system** with analyst-in-the-loop review:

1. **ML Deduplication** — Automatic entity matching using the [dedupe](https://github.com/dedupeio/dedupe) library, trained per entity type
2. **Analyst Review** — YAML-based merge authority (`entity_groups/*.yaml`) with DRAFT → CONFIRMED workflow
3. **Cross-Document Recovery** — Orphan relation resolver matches unresolved relations against the full graph using exact, fuzzy, and substring matching

Merges perform graph surgery: node consolidation, relation endpoint rewriting, metadata recomputation, and dangling reference cleanup.

## LLM Integration

Claude API integration with production reliability:

- **4-tier retry logic:** rate limit (exponential backoff) → timeout (model escalation) → empty response (model escalation) → connection error (simple retry)
- **Automatic model escalation:** Haiku → Sonnet on failure, balancing cost and reliability
- **Two-tier output posture:**
  - *Extraction (legal-grade):* Factual only — extracts what documents state
  - *Analysis (research-grade):* Interpretive — narratives, entity descriptions, document analyses
- **Cost-aware model selection:** Haiku for high-volume extraction (~$0.002/doc), Sonnet for narratives requiring reasoning

## Domain Configuration

The platform generalizes across domains through YAML-based configuration:

```yaml
# farmer_factory/domains/configs/cuban_property/domain.yaml
entity_types:
  - PERSON
  - PROPERTY
  - ORGANIZATION
  - LOCATION
  - DOCUMENT

relation_types:
  ownership: [OWNS, OWNED]
  transaction: [SOLD, SOLD_TO, BOUGHT, PURCHASED_FROM]
  succession: [INHERITED, HEIR_OF]
  expropriation: [CONFISCATED]
  family: [SPOUSE_OF, CHILD_OF, RELATED_TO]
  # ... 28 total
```

New domains (genealogy, Holocaust restitution, land claims) require a YAML config and prompt context file — no code changes.

## Verification Tiers

Every data point carries a verification tier:

| Tier | Label | Meaning |
|------|-------|---------|
| TIER_3 | AI-Generated | Raw LLM output, unreviewed |
| TIER_2 | Analyst-Verified | Reviewed and edited by human analyst |
| TIER_1 | Certified | Verified by credentialed legal reviewer |

Tier promotion is a human workflow, not automation. The platform surfaces AI output for review — it never certifies its own conclusions.

## CLI

23 commands managing the full processing lifecycle:

```bash
# Core pipeline
python -m farmer_factory.cli process CASE-ID              # OCR + extraction + graph
python -m farmer_factory.cli resolve-orphans CASE-ID       # Recover cross-doc relations
python -m farmer_factory.cli apply-merges CASE-ID          # Apply analyst-reviewed merges

# AI analysis (run after graph cleanup)
python -m farmer_factory.cli analyze CASE-ID               # Descriptions + analyses + narrative

# Entity resolution
python -m farmer_factory.cli train-deduplication CASE-ID --entity-type PERSON
python -m farmer_factory.cli rebuild-graph CASE-ID         # Regenerate from extractions

# Output
python -m farmer_factory.cli generate-dossier CASE-ID      # LaTeX PDF dossier
```

## Tech Stack

**Factory (Python)**
- Python 3.10+, Pydantic, NetworkX, Typer
- Google Cloud Vision (OCR), Anthropic Claude API (extraction + analysis)
- dedupe (ML entity resolution), Jinja2 + LaTeX (dossier generation)

**Vault (Next.js)**
- Next.js, TypeScript, Tailwind CSS, shadcn/ui
- react-force-graph-2d (knowledge graph visualization)
- 12 API routes, scroll-driven timeline with IntersectionObserver

## Quick Start

```bash
# Clone and set up Python environment
git clone https://github.com/juanceresa/forensic_analysis_platform.git
cd forensic_analysis_platform
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API keys
cp farmer_factory/.env.example farmer_factory/.env
# Edit .env with your Google Cloud Vision and Anthropic API keys

# Create a case
python -m farmer_factory.cli create-case --id MY-CASE --name "Case Name" --family "Family Name"

# Place document images in cases/MY-CASE/documents/
# Process
python -m farmer_factory.cli process MY-CASE
```

## Project Structure

```
farmer_factory/          # Python processing backend
├── cli.py               # 23-command Typer CLI
├── domains/             # YAML domain configurations
├── extract/             # LLM entity + relation extraction
├── intake/              # Document ingestion + case management
├── narrative/           # AI narrative generation
├── structure/           # Knowledge graph + entity resolution
│   ├── core/            # Graph builder + exporter
│   ├── dedupe/          # ML deduplication
│   └── merge/           # 3-layer merge engine
├── dossier/             # LaTeX PDF generation
└── prepare/             # Image preprocessing

farmer_vault/            # Next.js read-only frontend
├── app/                 # Pages + API routes
├── components/          # UI components (62 TSX)
└── lib/                 # Shared utilities

tests/                   # 232 tests across 46 files
```

## Research

This platform is part of a broader research program on civic AI infrastructure:

- [*The Civic LLM Working Paper*](https://osf.io/preprints/socarxiv/xuk2g_v1) — SocArXiv preprint on the democratic future of AI (basis for $5,000 GCP research grant)
- *The Democratic Ontology Deficit* — Submitted to *Philosophy & Technology* (under review)

## License

[AGPL-3.0](LICENSE) — Free to use, modify, and deploy. If you deploy a modified version as a service, you must open source your modifications.

## Author

**Juan Ceresa** — [GitHub](https://github.com/juanceresa) · [LinkedIn](https://linkedin.com/in/juanceresa)

Built at the Farmer House Democratic Repair Lab, Huston-Tillotson University, Austin TX.
