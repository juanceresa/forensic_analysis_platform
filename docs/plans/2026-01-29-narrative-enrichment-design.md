# Narrative Enrichment — Extended Thinking + Domain Context

**Date:** 2026-01-29
**Status:** Implementing

## Problem

The narrative page summarizes what documents say. It should explain what documents *mean* — connecting family records to historical context (Cuban agrarian law, sugar economics, confiscation timelines) and flagging forensic observations (discrepancies, missing records, patterns).

## Design

### 1. API Client: Extended Thinking Support

Add a separate `call_with_thinking()` method to `ClaudeAPIClient`. The existing `call_standard()` stays untouched — no signature changes, no risk to extraction callers.

```python
def call_with_thinking(
    self, prompt, model=None, max_retries=3, retry_delay=1.0,
    api_timeout=180, thinking_budget=10000, max_tokens=16000,
) -> Tuple[str, dict]:
    """Call Claude with extended thinking. Returns (text, usage_dict).

    usage_dict: {input_tokens, output_tokens, thinking_tokens, model, cost}
    """
```

**Behavior:**
- Pass `thinking={"type": "enabled", "budget_tokens": thinking_budget}`
- Omit `temperature` entirely (Anthropic requirement — API rejects temperature with thinking)
- Response parsing: iterate `response.content` blocks, return only the block with `type == "text"`, discard `type == "thinking"` blocks
- Returns `(text, usage_dict)` — usage dict built from `response.usage` with actual token counts and computed cost
- `api_timeout` defaults to 180s (more processing time than standard calls)

**`call_standard()` unchanged:** existing signature, return type (`str`), and behavior are preserved. Extraction pipeline untouched.

**Model guard:** if model doesn't contain `"sonnet"` or `"opus"`, log a warning and delegate to `call_standard()` instead (returns `(text, estimated_usage_dict)`). Extended thinking requires Sonnet or higher.

**Retry/downgrade path:**
- First attempt: Sonnet + thinking
- On failure: retry Sonnet + thinking (backoff)
- Final attempt: Haiku, no thinking (graceful downgrade, still produces output)

**Telemetry:** log per-call: model used, thinking enabled (bool), input_tokens, output_tokens, thinking_tokens (from `response.usage`), estimated cost. This data is already partially tracked via `_estimate_cost` but we'll use actual token counts from the API response instead of estimation.

### 2. Enriched Period Narrative Prompt

**Domain context injection:**
- Load `system_context.txt` from the active domain
- **Bound to 3000 chars max** — if longer, truncate with a `[truncated]` marker. This caps prompt bloat from unexpectedly large context files
- Injected as a `**Domain Knowledge:**` section between the existing context sections and the instructions

**Enriched instructions** — replace the current "write a narrative" block with:

```
**Instructions:**
First, write a short evocative title (3-6 words) for this period.

Then write a narrative (3-6 paragraphs) that does THREE things:

1. TELL THE STORY — what happened in this period, grounded in the documents.
   Use engaging language. Keep it accessible for families, not lawyers.

2. EXPLAIN THE SIGNIFICANCE — use your knowledge of the domain (see Domain
   Knowledge above) to explain WHY document details matter. Example: if a tax
   record lists 24 caballerías but other records show 60, explain what that
   discrepancy means in context of Cuban fiscal practices.

3. FLAG FORENSIC OBSERVATIONS — note discrepancies between documents, missing
   records one would expect, patterns that suggest something, or connections
   across documents the family might not see.

Weave all three naturally into the prose — do not use headers, bullets, or
separate sections. The narrative should read as one cohesive analytical story.

After the narrative, on a new line starting with "OBSERVATIONS:", list 1-3
brief forensic observations as pipe-separated entries:
  observation text | severity (HIGH/MEDIUM/LOW)

Output format:
<title>
---
<narrative prose>
---
OBSERVATIONS:
<observation> | <severity>
```

**Output structure:** The `---` delimiters give us three parseable sections:
1. Title (string)
2. Narrative prose (blended story + context + forensic insights)
3. Structured forensic observations (new field, surfaceable distinctly in UI)

### 3. New Model: ForensicObservation

```python
class ForensicObservation(BaseModel):
    observation: str
    severity: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
```

Add `forensic_observations: List[ForensicObservation]` to `NarrativePeriod`.

Parsing fallback: if the `OBSERVATIONS:` section is missing or malformed, `forensic_observations` defaults to empty list. No failure.

### 4. Narrative Generator Changes

**Domain context loading:**
- `CaseNarrativeGenerator.__init__()` accepts optional `domain_context: str`
- `generate()` loads from domain config path if not provided
- Truncated to 3000 chars before passing to prompt builder

**Thin period handling:**
- Periods with ≤1 document: skip thinking (`use_thinking=False`), use Haiku, `thinking_budget=0`. Not enough material to reason deeply — save the tokens.
- Periods with 2-3 documents: thinking with reduced budget (`thinking_budget=5000`)
- Periods with 4+ documents: full thinking (`thinking_budget=10000`)

**Per-period cost cap:** if `self.total_cost` exceeds 80% of `max_cost` mid-generation, remaining periods downgrade to Haiku without thinking. Logged as a warning.

**Actual token tracking:** `_call_llm` uses `call_with_thinking()` for thinking calls (returns usage dict with actual tokens) and `call_standard()` for non-thinking calls (estimates cost from prompt/response length). Both paths feed into `self.total_cost`.

```python
def _call_llm(self, prompt, use_thinking=False, thinking_budget=10000) -> Tuple[str, float]:
    """Returns (text, cost). Uses call_with_thinking() or call_standard() accordingly."""
```

**Summary call:** stays on Haiku without thinking (it's just synthesizing existing period narratives).

### 5. Cost Model

| Scenario | Model | Thinking | Est. tokens | Est. cost |
|----------|-------|----------|-------------|-----------|
| Thin period (≤1 doc) | Haiku | No | ~2K | $0.003 |
| Medium period (2-3 docs) | Sonnet | 5K budget | ~8K | $0.08 |
| Rich period (4+ docs) | Sonnet | 10K budget | ~15K | $0.15 |
| Summary | Haiku | No | ~3K | $0.004 |
| **Typical case (4 periods)** | | | | **$0.30-0.50** |

Well within `max_cost=2.0`. The 80% cost guard ensures we never exceed budget.

### 6. Frontend: Forensic Observations Display

Forensic observations render in **two** timeline components (Phase 9E split the
narrative page into a scroll experience and a static chronological view):

**A. `TimelinePeriod.tsx`** (static chronological view at `/narrative/chronological`)

After narrative prose, before highlighted events:

```tsx
{period.forensicObservations?.length > 0 && (
  <div className="mt-4 space-y-2">
    {period.forensicObservations.map((obs, i) => (
      <div key={i} className="flex items-start gap-2 px-3 py-2 rounded text-sm
                               bg-cyan-500/5 border border-cyan-500/15">
        <span className="shrink-0 text-cyan-400">◆</span>
        <span className="text-slate-300">{obs.observation}</span>
        <span className="ml-auto shrink-0 font-mono text-xs text-cyan-500/60">
          {obs.severity}
        </span>
      </div>
    ))}
  </div>
)}
```

**B. `ScrollEventNode.tsx`** (scroll experience at `/narrative`)

At reveal level 3 (full detail), after the document/parties line and before the
"Explore this event" link. Same markup adapted for scroll context — observations
are per-event, pulled from the enriched event data that `narrative/page.tsx`
builds by matching events to their period's `forensicObservations`:

```tsx
{revealLevel >= 3 && event.forensicObservations?.length > 0 && (
  <div className="scroll-reveal-full space-y-1.5">
    {event.forensicObservations.map((obs, i) => (
      <div key={i} className="flex items-start gap-2 px-3 py-1.5 rounded text-xs
                               bg-cyan-500/5 border border-cyan-500/15">
        <span className="shrink-0 text-cyan-400">◆</span>
        <span className="text-slate-400">{obs.observation}</span>
        <span className="ml-auto shrink-0 font-mono text-[10px] text-cyan-500/60">
          {obs.severity}
        </span>
      </div>
    ))}
  </div>
)}
```

**Data flow for scroll view:** `narrative/page.tsx` (server component) enriches
each event with its period's `forensicObservations` when building `enrichedEvents`,
the same way it already enriches with `narrative` text. `ScrollEventNode` receives
observations as a prop on `ScrollEventData`.

Timeline API passes `forensicObservations` from narrative data (both views consume
the same API response).

### 7. Logging & Validation

Every narrative LLM call logs:
```
INFO: Narrative LLM call: model=claude-sonnet-4-5, thinking=true, budget=10000,
      input_tokens=2847, output_tokens=1523, thinking_tokens=8241,
      cost=$0.14, cumulative=$0.22/$2.00
```

On downgrade:
```
WARN: Cost guard triggered ($1.62/$2.00), remaining periods downgrade to Haiku (no thinking)
```

On model fallback:
```
WARN: Sonnet+thinking failed, falling back to Haiku (no thinking)
```

## Files Modified

| File | Change |
|------|--------|
| `farmer_factory/extract/api_client.py` | `use_thinking`, `thinking_budget`, `max_tokens` params; thinking block filtering; actual token usage return |
| `farmer_factory/narrative/models.py` | `ForensicObservation` model, `forensic_observations` field on `NarrativePeriod` |
| `farmer_factory/narrative/prompts.py` | Domain context injection, enriched instructions, observations output format |
| `farmer_factory/narrative/generator.py` | Domain context loading, thin-period logic, cost guards, actual token tracking, observation parsing |
| `farmer_vault/app/api/cases/[caseId]/timeline/route.ts` | Pass `forensicObservations` per period |
| `farmer_vault/app/case/[caseId]/narrative/page.tsx` | Enrich events with period's `forensicObservations` |
| `farmer_vault/components/Narrative/TimelinePeriod.tsx` | Render forensic observations (static chronological view) |
| `farmer_vault/components/Timeline/ScrollEventNode.tsx` | Render forensic observations at reveal level 3 (scroll view) |

## Future: Perplexity API Layer

Not in this iteration. Future enhancement to bring in external research (specific mill histories, decree details, public records) that Claude's training data may not cover.
