# Case Narrative Generation Redesign

> **Date:** 2026-01-28
> **Status:** DESIGN

---

## Summary

Replace the on-demand, per-entity narrative generation with a batch, per-case narrative generated once during Factory processing. The narrative tells the family's story chronologically through documents, woven into the existing timeline periods on the AI Analysis tab.

## Architecture Change

| Aspect | Old | New |
|--------|-----|-----|
| Trigger | User clicks entity in UI | Factory `process` pipeline (every run regenerates) |
| Scope | Per-entity constellation | Entire case, per-period |
| Output | In-memory, session-cached | `case_narrative.json` static file |
| Delivery | POST API spawns Python | Vault reads static JSON |
| Cost model | Per-session $1 limit | One-time generation cost with caps |

## Output: `cases/{CASE-ID}/output/case_narrative.json`

```json
{
  "metadata": {
    "case_id": "TEST-CERESA",
    "generated_at": "2026-01-28T...",
    "model_used": "sonnet",
    "generation_cost": 0.045,
    "factory_version": "1.6.0"
  },
  "case_summary": "The Ceresa family's documentary record spans...",
  "periods": [
    {
      "period_id": "1950-1959",
      "label": "Pre-Revolution Era",
      "narrative": "During the 1950s, Mario Ceresa established...",
      "document_ids": ["doc_escritura_001"],
      "entity_ids": ["person_mario_001", "prop_villa_aurelia_001"],
      "highlighted_events": [
        {
          "event_type": "SOLD",
          "summary": "Villa Aurelia purchased by Mario Ceresa",
          "date": "1953-06-15"
        }
      ]
    }
  ]
}
```

## Factory Changes

### Generation Pipeline

1. Load `graph_data.json` (all entities, relations, documents)
2. Group documents by decade periods (same logic as Vault timeline API); merge adjacent sparse periods if each has <3 docs.
3. For each period: single LLM call with period context (documents, entities, relations)
4. Final LLM call for `case_summary` (informed by all period narratives)
5. Write `case_narrative.json` to `output/` (regenerated on every processing run)

### CLI Integration

```bash
# Runs as final step of process pipeline
python -m farmer_factory.cli process CASE-ID --domain cuban_property

# Standalone re-generation
python -m farmer_factory.cli generate-narrative CASE-ID
```

### Module Changes (`farmer_factory/narrative/`)

**Rewrite:**
- `generator.py` — batch chronological generation (per-period LLM calls)
- `prompts.py` — period-based forensic voice prompts
- `models.py` — `CaseNarrative` with period-keyed narratives

**Remove:**
- `constellation.py` — per-entity connected component extraction
- `scorer.py` — story centrality scoring
- `cache.py` — in-memory session cache
- `api/narrative.py` — Python API endpoint
- `scripts/generate_narrative.py` — subprocess CLI script

## Vault Changes

### API

- **Remove:** `POST /api/cases/[caseId]/narrative` (spawned Python subprocess)
- **Modify:** `GET /api/cases/[caseId]/timeline` — merge `case_narrative.json` data into period response

### Components

- `TimelinePeriod` — add `narrative` prop, render prose above document list
- `narrative/page.tsx` — render `case_summary` at top of page, below disclaimer

### Page Layout

```
┌─────────────────────────────────┐
│ AI Analysis              header │
│ 12 documents spanning 1950-2003│
├─────────────────────────────────┤
│ ⚠️ AI-Generated disclaimer      │
├─────────────────────────────────┤
│ Case Summary prose              │
├─────────────────────────────────┤
│ ▼ 1950-1959: Pre-Revolution    │
│   Period narrative prose...     │
│   📄 Doc 1  📄 Doc 2           │
│                                 │
│ ▼ 1959-1969: Expropriation     │
│   Period narrative prose...     │
│   📄 Doc 3                     │
└─────────────────────────────────┘
```

## Two Levels of AI Narrative

1. **Per-entity "About" blurb** — short, entity-scoped, shown in EntityDetail (existing)
2. **Case-level narrative** — full family story by period, shown on AI Analysis tab (this design)

Both are pre-generated during Factory processing. Both carry TIER_3_AI disclaimer. Per-entity blurbs continue to be generated in processing and rendered in the entity section.

## Verification

- [ ] `python -m farmer_factory.cli process TEST-CERESA` generates `case_narrative.json`
- [ ] `case_narrative.json` contains periods matching timeline decade grouping
- [ ] AI Analysis tab renders case summary and period narratives
- [ ] Period narratives appear above document lists in each TimelinePeriod
- [ ] TIER_3_AI disclaimer is visible
- [ ] Standalone `generate-narrative` CLI command works

## Cost Controls & Guardrails

- Per-period token cap and per-case max cost; abort with clear error if exceeded.
- Model downgrade on retry if cap approached/failed (e.g., sonnet→haiku).
- Deterministic prompts (no sampling) to keep token usage predictable.
- Always regenerate per processing run; no stale-cache reuse.

## Evidence & Provenance

- Include per-period `evidence` array (document_ids, relation_ids/event summaries) used for that narrative.
- Metadata: `model_used`, `model_version`, `prompt_hash`, `generation_cost`, `factory_version`, TIER_3_AI disclaimer.

## Generation Rules

- Decade-based periods. Empty periods allowed; merge adjacent sparse periods (<3 docs) before LLM call.
- Fail early if `graph_data.json` missing; graph assumed complete post-processing.

## Tests

- Unit: period grouping/merge logic (decades, sparse merge).
- Unit: cost guard enforcement (caps, downgrade path, abort).
- Unit: evidence population in `case_narrative.json`.
- Integration: processing sample case produces `case_narrative.json` with summary + periods.
- UI: AI Analysis renders summary + period narratives + disclaimer; handles missing narrative gracefully.
