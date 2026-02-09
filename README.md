# Civic Table

Forensic document intelligence platform for provenance-first case reconstruction.

Civic Table turns messy archival records into a structured evidence graph, timeline, and analyst-facing narrative while preserving verification posture:

- `TIER_3_AI`: machine-generated extraction/analysis
- `TIER_2_ANALYST`: human-reviewed
- `TIER_1_CERTIFIED`: credentialed legal certification

## Why This Exists

Most "document AI" stacks optimize for summarization speed.
This project optimizes for evidentiary traceability:

- where each claim came from
- how entities were inferred and merged
- what is still uncertain

The system is built around legal/audit-oriented workflows, not chatbot-style output.

## System Architecture

Two-zone architecture:

- `farmer_factory/`: processing zone (OCR, extraction, graph construction, narrative generation)
- `farmer_vault/`: read-only delivery zone (Next.js viewer + APIs)

Data flow is one-way: Factory -> Vault.

## Core Capabilities

- OCR ingestion + cleaned OCR text generation
- entity extraction across `PERSON`, `PROPERTY`, `ORGANIZATION`, `LOCATION`, `DOCUMENT`
- relation extraction + orphan relation recovery
- graph build/export (`graph_data.json`)
- analyst-controlled merge workflow with YAML review files
- narrative/timeline generation with inline entity linking
- document-level AI analysis (`document_analyses.json`)
- dossier PDF generation

## Public Repo Data Policy

This public repository does **not** include real client/family case files.

- real case data lives under local `cases/` (git-ignored)
- secrets stay in `.env` / `.env.local` (git-ignored)
- committed demo records under `examples/demo_case/` are synthetic

Before publishing this repository (or new history) run:

```bash
bash scripts/check_public_readiness.sh
```

If the history check fails because legacy private paths were committed in older
commits, rewrite history first:

```bash
bash scripts/sanitize_history_for_public_release.sh --yes-i-know-this-rewrites-history
```

## Fast Local Demo

From repository root:

```bash
# Python env (Factory)
python3 -m venv venv
source venv/bin/activate
pip install -r farmer_factory/requirements.txt

# Install synthetic demo case data into local /cases
bash scripts/install_demo_case.sh

# Start Vault UI
cd farmer_vault
npm install
npm run dev
```

Open:

`http://localhost:3000`

The app auto-selects an available local case and prefers `DEMO-SYNTHETIC`.

## Factory CLI

```bash
# Create a new case
python -m farmer_factory.cli create-case --id MY-CASE --name "My Case" --family "Family Name"

# End-to-end processing
python -m farmer_factory.cli process MY-CASE

# Graph cleanup / authority workflows
python -m farmer_factory.cli resolve-orphans MY-CASE
python -m farmer_factory.cli apply-merges MY-CASE

# AI analysis outputs
python -m farmer_factory.cli analyze MY-CASE
python -m farmer_factory.cli generate-analyses MY-CASE
python -m farmer_factory.cli generate-descriptions MY-CASE
python -m farmer_factory.cli generate-narrative MY-CASE
```

## Repository Layout

```text
farmer_factory/                Python pipeline + CLI
farmer_vault/                  Next.js viewer + API layer
examples/demo_case/            Synthetic public demo data template
scripts/install_demo_case.sh   One-command local demo installer
tests/                         Python test suite
docs/architecture/             Domain, frontend, security, and system docs
```

## Documentation

- architecture overview: `docs/architecture/ARCHITECTURE.md`
- security model: `docs/architecture/SECURITY.md`
- frontend domain model: `docs/architecture/FRONTEND.md`
- domain configuration: `docs/architecture/DOMAIN_CONFIGURATION.md`

## Security Notes

- do not commit `.env` or real case data
- use a strong `VAULT_PASSWORD`
- use a strong `VAULT_SESSION_SECRET` (used for signed session cookies)
- if exposing beyond localhost, run Vault with `NODE_ENV=production` so auth cookies are `secure`
- treat `TIER_3_AI` as non-authoritative until human review

See `SECURITY.md` for reporting and hardening policy.

## License

AGPL-3.0-only (`LICENSE`)

## Author

Juan Ceresa  
GitHub: `@juanceresa`
