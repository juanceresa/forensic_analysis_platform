# Civic Table

**Turn degraded archival documents into structured evidence.**

Civic Table is a forensic document intelligence platform that extracts entities, relationships, and timelines from historical records — then presents them as an interactive evidence graph with full provenance tracking.

Built for families pursuing property restitution claims, researchers working with degraded archives, and anyone who needs to reconstruct a documentary record where the paper trail is fragmented, multilingual, and decades old.

<!-- TODO: Add screenshot of Vault UI (dashboard, graph view, or timeline) -->
<!-- ![Civic Table — Case Dashboard](docs/assets/screenshot-dashboard.png) -->

## The Problem

A family has a box of 60-year-old scanned documents — deeds, wills, confiscation orders — in faded Spanish with OCR errors. They need to prove who owned what, when, and how ownership transferred. No existing tool does this without losing the chain of evidence.

## What Civic Table Does

1. **Ingests** scanned PDFs through OCR with LLM-powered text cleanup
2. **Extracts** people, properties, organizations, locations, and their relationships using Claude
3. **Builds** a knowledge graph with ML-powered entity deduplication and analyst-controlled merge workflows
4. **Generates** AI narratives, per-entity descriptions, document analyses, and a forensic PDF dossier
5. **Presents** everything in a read-only web interface with verification tiers on every data point

Every extracted fact carries a verification tier:

| Tier | Meaning |
|------|---------|
| `TIER_3_AI` | Machine-extracted, unverified |
| `TIER_2_ANALYST` | Human-reviewed and confirmed |
| `TIER_1_CERTIFIED` | Legally certified by external body |

Nothing is presented as truth until a human says it is.

## Architecture

Two-zone, air-gapped design. Processing and presentation are fully separated.

```text
farmer_factory/  (Python)          farmer_vault/  (Next.js)
─────────────────────────          ──────────────────────────
PDF Intake                         Case Dashboard
  -> Image Preprocessing           Entity Browser
  -> OCR (Google Cloud Vision)     Document Viewer (OCR + cleaned text)
  -> LLM Text Cleanup (Haiku)     Knowledge Graph (force-directed)
  -> Entity Extraction (Haiku)     Scroll-Driven Timeline
  -> Relation Extraction           AI Narrative Explorer
  -> Graph Build + Dedup           Forensic Dossier Download
  -> JSON Export ──────────────>   Read-Only API Layer
```

Data flows one direction: Factory produces JSON artifacts, Vault consumes them. Clients never touch the processing zone.

## Tech Stack

**Factory (Python):** Pydantic, NetworkX, Google Cloud Vision, Anthropic Claude API, dedupe (ML entity resolution)

**Vault (Next.js):** TypeScript, Tailwind CSS, shadcn/ui, react-force-graph-2d

**Infrastructure:** Domain-configurable (swap entity types and extraction prompts via YAML), case-level focus configuration, LaTeX dossier generation via XeLaTeX

## Quick Start

```bash
# Clone and set up Python environment
git clone https://github.com/juanceresa/forensic_analysis_platform.git
cd forensic_analysis_platform
python3 -m venv venv
source venv/bin/activate
pip install -r farmer_factory/requirements.txt

# Install synthetic demo case
bash scripts/install_demo_case.sh

# Start the Vault UI
cd farmer_vault
npm install
npm run dev
```

Open `http://localhost:3000` — the app auto-selects the demo case.

## Processing Pipeline (CLI)

```bash
# Create a case and add PDFs to cases/MY-CASE/intake/
python3 -m farmer_factory.cli create-case --id MY-CASE --name "My Case" --family "Family"

# Run the full extraction pipeline (OCR -> cleanup -> extraction -> graph)
python3 -m farmer_factory.cli process MY-CASE

# Post-processing: resolve orphan relations, review merges, apply
python3 -m farmer_factory.cli resolve-orphans MY-CASE
python3 -m farmer_factory.cli apply-merges MY-CASE

# Generate AI analysis (runs on the cleaned graph, not during processing)
python3 -m farmer_factory.cli analyze MY-CASE

# Generate forensic PDF dossier
python3 -m farmer_factory.cli generate-dossier MY-CASE \
  --property-id <PROPERTY_ENTITY_ID> \
  --family-member-id <PERSON_ENTITY_ID>
```

## Repository Layout

```text
farmer_factory/                Python processing pipeline + CLI
  domains/configs/             Domain configurations (entity types, relation types, prompts)
  extract/                     LLM entity/relation extraction
  narrative/                   AI narrative, descriptions, document analysis generation
  structure/                   Graph construction, dedup, merge engine
  dossier/                     LaTeX PDF dossier generator
farmer_vault/                  Next.js read-only viewer + API layer
tests/                         Python test suite
docs/                          Architecture, security, frontend, and operational docs
examples/demo_case/            Synthetic demo data
```

## Key Design Decisions

- **Verification tiers are not optional.** Every node and edge in the graph carries provenance metadata. The UI enforces this visually — unverified data is always labeled.
- **Entity merges require human review.** The system suggests merges via ML deduplication, but an analyst must confirm them in YAML authority files before they take effect.
- **AI analysis is separated from extraction.** The `process` command builds a raw graph. AI narratives and descriptions are generated later on the cleaned graph, so you don't burn credits on output you'll throw away during merge review.
- **Domain-configurable.** Entity types, relation types, and extraction prompts are defined in YAML, not hardcoded. The current domain is Cuban property restitution; the architecture supports genealogy, academic research, investigative journalism, or any documentary recovery domain.

## Data Policy

This repository does **not** contain real client or family case data.

- Case data lives under `cases/` (git-ignored)
- Secrets stay in `.env` / `.env.local` (git-ignored)
- Demo data under `examples/demo_case/` is synthetic

## Documentation

- [System Architecture](docs/architecture/ARCHITECTURE.md)
- [Domain Configuration](docs/architecture/DOMAIN_CONFIGURATION.md)
- [Frontend Architecture](docs/architecture/FRONTEND.md)
- [Security Model](docs/architecture/SECURITY.md)
- [CLI Usage Guide](docs/CLI_USAGE.md)
- [Analyst Guide](docs/guides/ANALYST_GUIDE.md)
- [Admin Guide](docs/guides/ADMIN_GUIDE.md)

## License

AGPL-3.0-only — see [LICENSE](LICENSE)

## Author

**Juan Ceresa** — [@juanceresa](https://github.com/juanceresa)

Built at the intersection of civic infrastructure, AI, and documentary recovery. Methodology developed at the Farmer House Democratic Repair Lab at Huston-Tillotson University.
