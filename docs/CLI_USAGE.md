# CLI Usage

## Environment Setup

Install Python deps:

```bash
pip install -r farmer_factory/requirements.txt
```

Optional system dependency for PDF handling (platform-specific):

- macOS: `brew install poppler`
- Ubuntu/Debian: `sudo apt-get install poppler-utils`

## Discover Commands

```bash
python3 -m farmer_factory.cli --help
```

List domains:

```bash
python3 -m farmer_factory.cli list-domains
```

## Core Workflow Commands

Create a case:

```bash
python3 -m farmer_factory.cli create-case --id CASE-001 --name "My Case" --family "Family" --domain cuban_property
```

Detect multi-part document groups:

```bash
python3 -m farmer_factory.cli detect-groups CASE-001
```

Process intake documents:

```bash
python3 -m farmer_factory.cli process CASE-001 --domain cuban_property
```

Validate graph export:

```bash
python3 -m farmer_factory.cli validate CASE-001 --domain cuban_property
```

Rebuild graph from saved extractions (no OCR/LLM rerun):

```bash
python3 -m farmer_factory.cli rebuild-graph CASE-001 --domain cuban_property
```

Apply confirmed merge authority:

```bash
python3 -m farmer_factory.cli apply-merges CASE-001 --domain cuban_property
```

Resolve orphan relations:

```bash
python3 -m farmer_factory.cli resolve-orphans CASE-001
```

Run AI analysis outputs:

```bash
python3 -m farmer_factory.cli analyze CASE-001 --max-cost 2.00 --domain cuban_property
```

## Analysis Subcommands

Generate entity descriptions only:

```bash
python3 -m farmer_factory.cli generate-descriptions CASE-001 --max-cost 0.50 --domain cuban_property
```

Generate document analyses only:

```bash
python3 -m farmer_factory.cli generate-analyses CASE-001 --max-cost 1.00 --domain cuban_property
```

Generate case narrative only:

```bash
python3 -m farmer_factory.cli generate-narrative CASE-001 --model sonnet --max-cost 2.00 --domain cuban_property
```

## Merge and Dedupe Commands

Train dedupe model(s):

```bash
python3 -m farmer_factory.cli train-deduplication CASE-001 --entity-type PERSON --num-examples 30 --domain cuban_property
```

Interactive group review:

```bash
python3 -m farmer_factory.cli review-groups CASE-001 --entity-type PERSON --domain cuban_property
```

Manual entity merge:

```bash
python3 -m farmer_factory.cli merge-entities CASE-001 entity_a entity_b --domain cuban_property
```

## Utility Commands

List cases:

```bash
python3 -m farmer_factory.cli list-cases
```

List entities:

```bash
python3 -m farmer_factory.cli list-entities CASE-001 --type PERSON
```

Generate dossier:

```bash
python3 -m farmer_factory.cli generate-dossier CASE-001 --property-id property_x --family-member-id person_y --domain cuban_property
```

Clean generated outputs (keeps intake and analyst authority files):

```bash
python3 -m farmer_factory.cli clean CASE-001 --confirm
```

Generate manifest from existing outputs:

```bash
python3 -m farmer_factory.cli generate-manifest CASE-001
```

## Placeholder Commands

These commands exist but are currently placeholders in this codebase:

- `upload`
- `retry`
- `retry-relations`

Check command help output before integrating them into automation.
