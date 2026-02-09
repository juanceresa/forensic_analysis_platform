# Testing Strategy

## Goal

Keep extraction, graph construction, and delivery behavior stable as prompts, schemas, and merge logic evolve.

## Test Layers

1. Unit tests
- schema validation
- prompt builder behavior
- merge reader/writer/engine behavior
- utility functions and route helpers

2. Component/integration tests
- API route behavior for case/document/entity lookups
- document grouping resolution
- graph serialization and validation

3. Workflow verification
- command-level checks for process/rebuild/analyze paths
- manual spot checks in Vault for rendered outputs

## Suggested Local Commands

From repository root:

```bash
# Python tests
pytest tests/ -x --ignore=tests/extract/test_integration.py --ignore=tests/golden/

# Focused tests (example)
pytest tests/intake/test_case_focus.py -v
```

From `farmer_vault/`:

```bash
npm test
npm run lint
npm run type-check
```

## Quality Gates Before Sharing Results

1. `graph_data.json` validates.
2. confirmed merge files apply cleanly.
3. key API endpoints return expected payload shape.
4. critical UI views load: documents, entity detail, graph, narrative.
5. AI-generated outputs are clearly treated as non-authoritative until analyst review.

## Regression Priorities

Pay special attention to:

- entity ID stability and merge-map rewrites
- grouped-document provenance mapping
- relation extraction precision on family relations
- compatibility of optional outputs (`entity_descriptions.json`, `document_analyses.json`)
