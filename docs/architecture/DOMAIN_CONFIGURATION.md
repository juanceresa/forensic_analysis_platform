# Domain Configuration

## Purpose

Domain configuration lets the same pipeline operate across different documentary domains without hardcoding entity/relation semantics in Python code.

Current default domain: `cuban_property`.

## Where It Lives

- domain loader/registry: `farmer_factory/domains/`
- domain configs: `farmer_factory/domains/configs/<domain>/domain.yaml`
- prompt context files: domain-specific prompt assets under each config

## What Domain Config Controls

1. Entity model surface
- Valid entity types available for extraction and validation.

2. Relation model surface
- Valid relation types and their semantics.
- Temporal/state behavior used downstream in graph logic.

3. Extraction guidance
- Domain context injected into extraction prompts.
- Relation extraction hints and language-specific cues.

4. Validation boundaries
- Graph/schema validation aligned to active domain types.

## Runtime Behavior

CLI commands accept `--domain` (default `cuban_property`).

At command start:

1. domain is loaded via registry
2. active type enums are refreshed
3. extraction and validation use that active domain

## Case-Level Focus vs Domain-Level Context

Domain config is global semantics.

Case focus (`cases/<CASE_ID>/case.yaml`) is analyst intent for a single case:

- `primary_subjects`
- `primary_assets`
- `focus_context`

Case focus is threaded into interpretive prompt generation paths so narratives and analyses emphasize the right story while retaining broader context.

## Creating a New Domain

1. Add `farmer_factory/domains/configs/<new_domain>/domain.yaml`.
2. Define entity and relation types required by that domain.
3. Add domain prompt/context assets.
4. Validate with `python3 -m farmer_factory.cli list-domains`.
5. Process a case with `--domain <new_domain>`.

## Practical Guidance

- Keep domain definitions minimal and explicit.
- Prefer adding extraction hints over adding brittle prompt complexity.
- Introduce new relation types only when they are analytically necessary and reviewable.
