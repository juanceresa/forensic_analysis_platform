# Narrative Module

> **Version:** 2.0.0
> **Last Updated:** 2026-02-07
> **Status:** Batch generation (case narratives + entity descriptions)

Batch narrative generation for forensic intelligence cases. Produces case-level timeline narratives and per-entity prose descriptions.

---

## Module Structure

```
narrative/
├── models.py               # Pydantic: CaseNarrative, NarrativePeriod, EventHighlight
├── prompts.py              # LLM prompt templates (period + summary)
├── generator.py            # CaseNarrativeGenerator (batch, period-based)
└── entity_descriptions.py  # Per-entity description generator (Haiku)
```

---

## 1. Case Narrative Generation (`generator.py`)

Batch per-case narrative generation. Produces `case_narrative.json` with period-based narratives organized by decade.

### Usage

```bash
# Runs automatically during `process` pipeline
python -m farmer_factory.cli process CASE-ID

# Or standalone
python -m farmer_factory.cli generate-narrative CASE-ID
```

### Architecture

- **Grouping:** Documents grouped by decade, sparse periods merged
- **Model:** Sonnet for narrative quality, Haiku fallback on cost limit
- **Cost control:** Configurable max cost ($2 default), model downgrade on failure
- **Output:** `cases/{CASE_ID}/output/case_narrative.json`

### Output Schema

```json
{
  "metadata": { "case_id": "...", "model": "...", "cost": 0.12 },
  "case_summary": "Overall case narrative...",
  "periods": [
    {
      "start_year": 1950, "end_year": 1959,
      "title": "Acquisition Period",
      "narrative": "During the 1950s...",
      "events": [
        { "year": 1958, "event_type": "SOLD", "summary": "...", "parties": [...] }
      ]
    }
  ]
}
```

### Event Highlighting

Special prominence for key events:
- **CONFISCATED** — Expropriations (red highlight in Vault UI)
- **SOLD** — Property sales
- **INHERITED** — Estate transfers

---

## 2. Entity Description Generation (`entity_descriptions.py`)

Per-entity AI-generated prose descriptions using Haiku for cost control.

### Usage

```bash
python -m farmer_factory.cli generate-descriptions CASE-ID
```

### Architecture

- **Model:** Haiku (~$0.0016/entity, ~$0.03 for 18-entity case)
- **Incremental:** Re-running skips entities already described
- **Separate file:** Writes to `entity_descriptions.json` (survives graph rebuilds)
- **Skips DOCUMENT entities:** Only describes PERSON, PROPERTY, ORGANIZATION, LOCATION

### Output

```json
{
  "person_mario_ceresa_001": "Mario Ceresa appears in multiple notarial documents...",
  "property_villa_aurelia_001": "Villa Aurelia is a residential property located in..."
}
```

### Design Decisions

- **Separate file:** `entity_descriptions.json` lives alongside `graph_data.json` but is not embedded in it. This means descriptions survive `rebuild-graph` and `apply-merges` operations.
- **Haiku model:** Cheap enough to regenerate freely (~$0.001/entity)
- **Forensic voice:** Descriptions state only what documents show, never make legal conclusions

---

## Vault Integration

### Case Narrative
- Timeline API reads `case_narrative.json`, merges into period responses
- Scroll-driven timeline experience renders periods with progressive reveal
- Key events surfaced in entity browser index page

### Entity Descriptions
- Entity detail API merges descriptions from `entity_descriptions.json`
- Displayed in "About" section with TIER_3_AI disclaimer badge
- Falls back gracefully when descriptions file doesn't exist

---

## Testing

```bash
# Unit tests (safe — no API calls)
pytest tests/narrative/ -v

# 27 tests covering models, prompts, generator
```

---

## See Also

- Redesign: `docs/plans/2026-01-28-case-narrative-generation-redesign.md`
- Prompts: `farmer_factory/narrative/prompts.py`
- Schema: `farmer_factory/narrative/models.py`
