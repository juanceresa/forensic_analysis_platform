# Event Narrative + Case Distillation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure narrative generation from period-oriented to event-oriented, and add a new Case Distillation feature (Sonnet, once per case) as an AI Analysis sub-tab.

**Architecture:** Replace period prose generation with two new pipelines: `_generate_event_narrative()` (Haiku, per-event, 2-4 paragraph rich historical narratives with period context injected) and `_generate_case_distillation()` (Sonnet, once per case, cross-event forensic intelligence). `case_narrative.json` keeps `periods` as structural containers (documents, entities, date ranges — `narrative: null`) and adds `event_narratives` dict + `distillation` object. Scroll experience renders period headlines as section dividers with events nested underneath.

**Tech Stack:** Python (Pydantic, Anthropic API), Next.js (TypeScript, Tailwind CSS)

---

## Context

### Current State
- `generator.py` generates **period narratives** (Sonnet, per-decade) — 3-6 paragraph prose per period
- Timeline API constructs **events** from `highlighted_events` + implicit FILED events, plus `periods` with decade groupings
- Scroll experience (`ScrollEventNode.tsx`) shows events with progressive reveal but borrows period narrative as snippet
- Event detail page (`event/[eventId]/page.tsx`) shows the period narrative, not event-specific content
- Chronological view (`/narrative/chronological`) renders `TimelinePeriod` components from `periods` array

### Target State
- **Event Narratives** (Haiku, per-event): Rich 2-4 paragraph historical narratives grounded in the specific event's documents, entities, and relations. Each event is generated with its parent period's label and date range as context so Claude can frame events historically. Powers both scroll view snippets and expanded event detail pages.
- **Case Distillation** (Sonnet, once per case): Cross-event forensic intelligence report — patterns, discrepancies, chains of custody, strategic observations. New sub-tab under AI Analysis. Absorbs the synthetic "big picture" role that period narratives previously served.
- **Periods as structural containers + visual dividers** — `periods` array stays in `case_narrative.json` with document lists, entity lists, date ranges, and `highlighted_events`. `narrative` field set to `null` — no LLM calls for period prose. Periods serve as section headlines in the scroll experience.

### Scroll Experience Layout
```
Hero Section (100vh)

--- Expropriation Period (1959-1961) ---    ← period headline on spine
    evt: CONFISCATED · Villa Aurelia · 1960  ← event node (60vh, progressive reveal)
    evt: FILED · Resolution 123 · 1960       ← event node

--- Post-War Era (1945-1958) ---             ← period headline
    evt: INHERITED · Mario Ceresa · 1955
    evt: FILED · Escritura 482 · 1952
    evt: SOLD · Finca Las Mercedes · 1948

--- continues ---

Geolocation (placeholder)
Knowledge Graph (placeholder)
```

Each period headline is a visual divider on the sticky spine — not collapsible, just a contextual marker. Events render chronologically within their period.

### Cost Model
- **Before:** ~3-5 Sonnet calls (one per period + summary) ≈ $0.30-0.50/case
- **After:** ~10-20 Haiku calls (per-event, capped at 30) + 1 Sonnet call (distillation) ≈ $0.05-0.15/case
- Net savings: ~60-80% cost reduction

### Design Decisions (from review)
1. **Schema version** — `NarrativeMetadata.factory_version` bumped to `"2.0.0"` to signal the new shape. Consumers check: if `event_narratives` key exists → v2 (event-driven); if only `periods` with non-null narratives → v1 (period-driven). Timeline API branches on this.
2. **Periods kept as structure, not prose** — periods retain document/entity/date-range groupings for the chronological view. `narrative` field set to `null`. No LLM calls for period text. `NarrativePeriod` model stays but `_generate_period()` removed.
3. **Event count cap** — `max_events=30` default. Highlighted events (CONFISCATED/SOLD/INHERITED) always included. FILED events fill remaining slots by chronological order. When capped, `NarrativeMetadata` gets `events_truncated: bool` and `total_events_found: int` so consumers know about silent drops.
4. **Event construction** — mirrors timeline API logic: CONFISCATED/SOLD/INHERITED from graph relations + FILED from documents. Deterministic `evt_N` IDs by chronological order. Dedupe: same type + year + parties = one event.
5. **Observation cap for distillation** — top 10 by severity (HIGH first) to avoid token bloat.
6. **Distillation parsing fallback** — if no markdown headers found, entire response treated as `executive_summary` with empty other fields.
7. **Integration test** — added as Task 11 with fixture graph.

---

## Task 1: Add Event Narrative Model

**Files:**
- Modify: `farmer_factory/narrative/models.py`
- Test: `tests/narrative/test_generator.py`

**Step 1: Write the failing test**

```python
# In tests/narrative/test_generator.py, add at top-level:
def test_event_narrative_model():
    from farmer_factory.narrative.models import EventNarrative
    en = EventNarrative(
        event_id="evt_0",
        event_type="CONFISCATED",
        year=1960,
        title="The Seizure of Villa Aurelia",
        narrative="INRA agents arrived at Villa Aurelia...\n\nThe confiscation order...",
        document_ids=["d1"],
        entity_ids=["e1", "e2"],
        parties=["INRA", "Mario Ceresa"],
        forensic_observations=[],
        inline_entities=[],
    )
    assert en.event_id == "evt_0"
    assert en.year == 1960
    assert len(en.narrative) > 0
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/narrative/test_generator.py::test_event_narrative_model -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

Add to `farmer_factory/narrative/models.py`:

```python
class EventNarrative(BaseModel):
    """AI-generated narrative for a single event."""

    event_id: str = Field(description="Event identifier (e.g., 'evt_0')")
    event_type: str = Field(description="CONFISCATED, SOLD, INHERITED, FILED")
    year: int = Field(description="Event year")
    date: Optional[str] = Field(default=None, description="Specific date if known")
    title: str = Field(default="", description="Short evocative title for the event")
    summary: str = Field(default="", description="One-line summary")
    narrative: str = Field(description="Rich 2-4 paragraph narrative")
    document_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    parties: List[str] = Field(default_factory=list)
    forensic_observations: List[ForensicObservation] = Field(default_factory=list)
    inline_entities: List[InlineEntity] = Field(default_factory=list)
```

Also add `CaseDistillation` model:

```python
class CaseDistillation(BaseModel):
    """Sonnet-generated cross-event forensic intelligence report."""

    executive_summary: str = Field(description="2-3 paragraph executive summary")
    ownership_chain: str = Field(description="Documented chain of custody narrative")
    forensic_findings: List[ForensicObservation] = Field(default_factory=list)
    evidentiary_gaps: List[str] = Field(default_factory=list, description="Missing records or unexplained gaps")
    cross_event_patterns: List[str] = Field(default_factory=list, description="Patterns across events")
    period_titles: Dict[str, str] = Field(
        default_factory=dict,
        description="LLM-generated evocative titles keyed by period_id (e.g. '1959-1961': 'The Confiscation')",
    )
```

Update `NarrativeMetadata` — bump version and add truncation fields:

```python
# In NarrativeMetadata:
    factory_version: str = Field(default="2.0.0", description="2.0.0 = event-driven schema")
    events_truncated: bool = Field(default=False, description="True if events exceeded max_events cap")
    total_events_found: int = Field(default=0, description="Total events before truncation")
```

Update `CaseNarrative` — keep `periods` as structural containers, add new fields:

```python
class CaseNarrative(BaseModel):
    metadata: NarrativeMetadata
    case_summary: str = Field(description="Overall case narrative summary")
    periods: List[NarrativePeriod] = Field(
        default_factory=list,
        description="Structural period groupings (no LLM prose — narrative field is null)",
    )
    event_narratives: Dict[str, EventNarrative] = Field(
        default_factory=dict,
        description="Event narratives keyed by event_id",
    )
    distillation: Optional[CaseDistillation] = Field(
        default=None,
        description="Sonnet-generated forensic intelligence report",
    )
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/narrative/test_generator.py::test_event_narrative_model -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/models.py tests/narrative/test_generator.py
git commit -m "feat: add EventNarrative and CaseDistillation models"
```

---

## Task 2: Add Event Narrative Prompt

**Files:**
- Modify: `farmer_factory/narrative/prompts.py`
- Test: `tests/narrative/test_generator.py`

**Step 1: Write the failing test**

```python
def test_build_event_prompt():
    from farmer_factory.narrative.prompts import build_event_prompt
    prompt = build_event_prompt(
        event_type="CONFISCATED",
        event_summary="INRA confiscated Villa Aurelia",
        year=1960,
        date="1960-03-15",
        documents=[{"id": "d1", "name": "Resolution 123", "date": "1960-03-15", "document_type": "Government Resolution"}],
        entities=[{"id": "e1", "name": "Villa Aurelia", "entity_type": "PROPERTY"}],
        relations=[{"relation_type": "CONFISCATED", "source_name": "INRA", "target_name": "Villa Aurelia", "date": "1960"}],
        parties=["INRA", "Mario Ceresa"],
        domain_context="Cuban property restitution context...",
    )
    assert "CONFISCATED" in prompt
    assert "Villa Aurelia" in prompt
    assert "1960" in prompt
    assert "Domain Knowledge" in prompt
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/narrative/test_generator.py::test_build_event_prompt -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

Add to `farmer_factory/narrative/prompts.py`:

```python
EVENT_NARRATIVE_TEMPLATE = """You are a forensic analyst writing a detailed historical narrative about a specific event in a property restitution case.

**CRITICAL CONSTRAINTS:**
1. Write in past tense with engaging, in-depth narrative voice
2. NEVER make legal conclusions or assess ownership validity
3. NEVER infer beyond what the documents explicitly state
4. Ground every claim in the documents provided — do not fabricate
5. Write 2-4 substantial paragraphs — this is the primary narrative for this event

**Historical Period:** {period_label} ({period_range})
**Event:** {event_type} — {event_summary}
**Year:** {year}
**Date:** {date}
**Parties:** {parties}

**Documents related to this event:**
{documents_context}

**Entities involved:**
{entities_context}

**Relations:**
{relations_context}
{domain_knowledge}
**Instructions:**
First, write a short evocative title (3-6 words) — something a family would recognize,
like "The Seizure of Villa Aurelia" or "A Father's Final Purchase".

Then write a rich historical narrative (2-4 paragraphs) that:

1. RECONSTRUCTS THE EVENT — what happened, who was involved, what documents record it.
   Use specific names, dates, and document references. Make it vivid and accessible.

2. PROVIDES CONTEXT — use your domain knowledge to explain why this event matters.
   What did it mean for the family? What was happening historically?

3. FLAGS FORENSIC DETAILS — note anything unusual in the documents: discrepancies,
   missing information one would expect, connections across documents.

The narrative should read as one cohesive analytical story — not bullets or lists.

After the narrative, on a new line starting with "OBSERVATIONS:", list 0-3
brief forensic observations as pipe-separated entries:
  observation text | severity (HIGH/MEDIUM/LOW)

Output format:
<title>
---
<narrative prose>
---
OBSERVATIONS:
<observation> | <severity>"""


CASE_DISTILLATION_TEMPLATE = """You are a senior forensic intelligence analyst producing a comprehensive case distillation report.

**CRITICAL CONSTRAINTS:**
1. Synthesize across ALL events — do not summarize individual events sequentially
2. NEVER make legal conclusions or assess ownership validity
3. Focus on forensic intelligence: patterns, discrepancies, chains of custody
4. This is the most important analytical output of the entire case

**Case:** {case_id}
**Date Range:** {date_range}
**Total Documents:** {total_documents}
**Total Events:** {total_events}

**Time Periods:**
{period_list}

**Event Summaries (chronological):**
{event_summaries}

**All Forensic Observations:**
{all_observations}
{domain_knowledge}
**Instructions:**
Produce a forensic intelligence report with these sections (use markdown headers):

## Period Titles
For each time period listed above, write a short evocative title (3-6 words) that a family
would recognize — like "The Confiscation" or "Building The Family Empire" or "A Legacy Divided".
Format as one line per period:
period_id | title

## Executive Summary
2-3 paragraphs synthesizing the full arc of this case. What do the documents tell us?
What is the family's documented history with these properties?

## Chain of Custody
Trace documented ownership/control transfers chronologically. Note where the chain
is well-documented vs where gaps exist. Be specific about which documents establish
each link.

## Forensic Findings
Bullet list of significant findings:
- Discrepancies between documents
- Missing records one would expect
- Patterns suggesting specific historical processes
- Cross-document corroboration (or contradiction)

## Evidentiary Gaps
Bullet list of gaps in the documentary record that an analyst should investigate:
- Time periods with no documentation
- Expected documents that are absent
- Questions raised by existing documents

Output ONLY the report in markdown format."""


def build_event_prompt(
    event_type: str,
    event_summary: str,
    year: int,
    date: str | None,
    period_label: str,
    period_range: str,
    documents: list[dict],
    entities: list[dict],
    relations: list[dict],
    parties: list[str],
    domain_context: str = "",
) -> str:
    """Build prompt for a single event's narrative generation."""
    docs_lines = []
    for doc in documents:
        line = f"- {doc.get('name', doc.get('id', 'Unknown'))}"
        if doc.get("date"):
            line += f" (dated {doc['date']})"
        if doc.get("document_type"):
            line += f" [{doc['document_type']}]"
        docs_lines.append(line)
    docs_str = "\n".join(docs_lines) or "No documents available."

    entity_lines = [
        f"- {e.get('name', '?')} ({e.get('entity_type', 'UNKNOWN')})"
        for e in entities
    ]
    entities_str = "\n".join(entity_lines) or "No entities identified."

    relation_lines = []
    for rel in relations:
        line = f"- {rel.get('relation_type', '?')}: {rel.get('source_name', '?')} -> {rel.get('target_name', '?')}"
        if rel.get("date"):
            line += f" (date: {rel['date']})"
        relation_lines.append(line)
    relations_str = "\n".join(relation_lines) or "No relations identified."

    domain_section = ""
    if domain_context:
        truncated = domain_context[:3000]
        if len(domain_context) > 3000:
            truncated += "\n[truncated]"
        domain_section = f"\n**Domain Knowledge:**\n{truncated}\n"

    return EVENT_NARRATIVE_TEMPLATE.format(
        event_type=event_type,
        event_summary=event_summary,
        year=year,
        date=date or "Unknown",
        period_label=period_label,
        period_range=period_range,
        parties=", ".join(parties) if parties else "Unknown",
        documents_context=docs_str,
        entities_context=entities_str,
        relations_context=relations_str,
        domain_knowledge=domain_section,
    )


def build_distillation_prompt(
    case_id: str,
    date_range: str,
    total_documents: int,
    total_events: int,
    periods: list[dict],
    event_summaries: list[dict],
    all_observations: list[dict],
    domain_context: str = "",
) -> str:
    """Build prompt for the case distillation report."""
    period_lines = []
    for p in periods:
        period_lines.append(
            f"- {p.get('period_id', '?')} ({p.get('label', '?')}): "
            f"{p.get('document_count', 0)} documents, {p.get('entity_count', 0)} entities"
        )
    period_str = "\n".join(period_lines) or "No periods."

    summaries_lines = []
    for es in event_summaries:
        summaries_lines.append(
            f"**{es.get('year', '?')} — {es.get('event_type', '?')}:** {es.get('summary', '')}"
        )
    summaries_str = "\n".join(summaries_lines)

    obs_lines = []
    for obs in all_observations:
        obs_lines.append(f"- [{obs.get('severity', 'MEDIUM')}] {obs.get('observation', '')}")
    obs_str = "\n".join(obs_lines) or "No forensic observations flagged."

    domain_section = ""
    if domain_context:
        truncated = domain_context[:3000]
        if len(domain_context) > 3000:
            truncated += "\n[truncated]"
        domain_section = f"\n**Domain Knowledge:**\n{truncated}\n"

    return CASE_DISTILLATION_TEMPLATE.format(
        case_id=case_id,
        date_range=date_range,
        total_documents=total_documents,
        total_events=total_events,
        period_list=period_str,
        event_summaries=summaries_str,
        all_observations=obs_str,
        domain_knowledge=domain_section,
    )
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/narrative/test_generator.py::test_build_event_prompt -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/prompts.py tests/narrative/test_generator.py
git commit -m "feat: add event narrative and case distillation prompt templates"
```

---

## Task 3: Restructure Generator — Event Narratives

**Files:**
- Modify: `farmer_factory/narrative/generator.py`
- Test: `tests/narrative/test_generator.py`

**Step 1: Write the failing test**

```python
class TestEventNarrativeGeneration:
    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_generate_event_narrative(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        mock_client.call_standard.return_value = (
            "The Seizure\n---\nINRA agents arrived at Villa Aurelia in March 1960.\n\n"
            "The confiscation order bore the signature of the local INRA delegate.\n---\n"
            "OBSERVATIONS:\nNo prior notice documented | HIGH"
        )

        gen = CaseNarrativeGenerator(api_key="test", max_cost=10.0, primary_model="haiku")
        gen.domain_context = ""
        event_narrative = gen._generate_event_narrative(
            event_id="evt_0",
            event_type="CONFISCATED",
            event_summary="INRA confiscated Villa Aurelia",
            year=1960,
            date="1960-03-15",
            documents=[{"id": "d1", "name": "Resolution 123", "date": "1960-03-15"}],
            entities=[{"id": "e1", "name": "Villa Aurelia", "entity_type": "PROPERTY"}],
            relations=[{"relation_type": "CONFISCATED", "source_name": "INRA", "target_name": "Villa Aurelia"}],
            parties=["INRA", "Mario Ceresa"],
        )
        assert event_narrative.title == "The Seizure"
        assert "INRA agents" in event_narrative.narrative
        assert len(event_narrative.forensic_observations) == 1
        assert event_narrative.forensic_observations[0].severity == "HIGH"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/narrative/test_generator.py::TestEventNarrativeGeneration -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

In `generator.py`, add `_generate_event_narrative()` method to `CaseNarrativeGenerator`:

```python
def _generate_event_narrative(
    self,
    event_id: str,
    event_type: str,
    event_summary: str,
    year: int,
    date: str | None,
    period_label: str,
    period_range: str,
    documents: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    parties: list[str],
) -> "EventNarrative":
    """Generate a rich narrative for a single event using Haiku."""
    from farmer_factory.narrative.prompts import build_event_prompt

    prompt = build_event_prompt(
        event_type=event_type,
        event_summary=event_summary,
        year=year,
        date=date,
        period_label=period_label,
        period_range=period_range,
        documents=documents,
        entities=entities,
        relations=relations,
        parties=parties,
        domain_context=self.domain_context,
    )

    # Force Haiku for event narratives (cheap per-event)
    old_primary = self.primary_model
    self.primary_model = "haiku"
    try:
        raw_text, cost = self._call_llm(prompt)
    finally:
        self.primary_model = old_primary

    title, narrative_text, forensic_observations = self._parse_enriched_response(
        raw_text, fallback_title=event_summary
    )

    inline_entities = self._match_inline_entities(narrative_text, entities)

    return EventNarrative(
        event_id=event_id,
        event_type=event_type,
        year=year,
        date=date,
        title=title,
        summary=event_summary,
        narrative=narrative_text,
        document_ids=[d["id"] for d in documents],
        entity_ids=[e["id"] for e in entities],
        parties=parties,
        forensic_observations=forensic_observations,
        inline_entities=inline_entities,
    )
```

Update imports at top of generator.py to include `EventNarrative`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/narrative/test_generator.py::TestEventNarrativeGeneration -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/generator.py tests/narrative/test_generator.py
git commit -m "feat: add _generate_event_narrative method (Haiku, per-event)"
```

---

## Task 4: Restructure Generator — Case Distillation

**Files:**
- Modify: `farmer_factory/narrative/generator.py`
- Test: `tests/narrative/test_generator.py`

**Step 1: Write the failing test**

```python
class TestCaseDistillation:
    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_generate_distillation(self, mock_client_cls):
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        mock_client.call_standard.return_value = (
            "## Executive Summary\nThe Ceresa family...\n\n"
            "## Chain of Custody\nVilla Aurelia was purchased...\n\n"
            "## Forensic Findings\n- Tax records show discrepancy\n\n"
            "## Evidentiary Gaps\n- No inheritance filing for 1955"
        )

        gen = CaseNarrativeGenerator(api_key="test", max_cost=10.0, primary_model="sonnet")
        gen.domain_context = ""

        from farmer_factory.narrative.models import EventNarrative, ForensicObservation
        event_narratives = {
            "evt_0": EventNarrative(
                event_id="evt_0", event_type="CONFISCATED", year=1960,
                title="The Seizure", summary="INRA confiscated Villa Aurelia",
                narrative="...", document_ids=["d1"], entity_ids=["e1"],
                parties=["INRA"],
                forensic_observations=[ForensicObservation(observation="No notice", severity="HIGH")],
            ),
        }

        distillation = gen._generate_distillation(
            case_id="TEST",
            date_range="1950-1960",
            total_documents=5,
            event_narratives=event_narratives,
        )
        assert "Ceresa family" in distillation.executive_summary
        assert "Villa Aurelia" in distillation.ownership_chain
        assert len(distillation.forensic_findings) > 0
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/narrative/test_generator.py::TestCaseDistillation -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

Add `_generate_distillation()` and `_parse_distillation_response()` to `CaseNarrativeGenerator`:

```python
def _generate_distillation(
    self,
    case_id: str,
    date_range: str,
    total_documents: int,
    narrative_periods: list["NarrativePeriod"],
    event_narratives: dict[str, "EventNarrative"],
) -> "CaseDistillation":
    """Generate cross-event forensic intelligence report + period titles using Sonnet."""
    from farmer_factory.narrative.prompts import build_distillation_prompt

    # Build period info for title generation
    periods_info = []
    for p in narrative_periods:
        periods_info.append({
            "period_id": p.period_id,
            "label": p.label,
            "document_count": len(p.document_ids),
            "entity_count": len(p.entity_ids),
        })

    # Build event summaries and collect all observations (top 10 by severity)
    event_summaries = []
    all_observations = []
    for en in sorted(event_narratives.values(), key=lambda e: e.year):
        event_summaries.append({
            "year": en.year,
            "event_type": en.event_type,
            "summary": en.summary,
        })
        for obs in en.forensic_observations:
            all_observations.append({
                "observation": obs.observation,
                "severity": obs.severity,
            })

    # Cap observations: HIGH first, then MEDIUM, then LOW — max 10
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_observations.sort(key=lambda o: severity_order.get(o["severity"], 2))
    all_observations = all_observations[:10]

    prompt = build_distillation_prompt(
        case_id=case_id,
        date_range=date_range,
        total_documents=total_documents,
        total_events=len(event_narratives),
        periods=periods_info,
        event_summaries=event_summaries,
        all_observations=all_observations,
        domain_context=self.domain_context,
    )

    # Force Sonnet for distillation
    old_primary = self.primary_model
    self.primary_model = "sonnet"
    try:
        raw_text, cost = self._call_llm(prompt)
    finally:
        self.primary_model = old_primary

    return self._parse_distillation_response(raw_text)

@staticmethod
def _parse_distillation_response(raw_text: str) -> "CaseDistillation":
    """Parse markdown-formatted distillation response."""
    from farmer_factory.narrative.models import CaseDistillation, ForensicObservation

    sections = {"period_titles": "", "executive_summary": "", "ownership_chain": "", "forensic_findings": [], "evidentiary_gaps": []}

    current_section = None
    current_lines: list[str] = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        header_lower = stripped.lower().replace("#", "").strip()

        if header_lower.startswith("period titles"):
            if current_section:
                sections[current_section] = _join_section(current_lines, current_section)
            current_section = "period_titles"
            current_lines = []
        elif header_lower.startswith("executive summary"):
            if current_section:
                sections[current_section] = _join_section(current_lines, current_section)
            current_section = "executive_summary"
            current_lines = []
        elif header_lower.startswith("chain of custody"):
            if current_section:
                sections[current_section] = _join_section(current_lines, current_section)
            current_section = "ownership_chain"
            current_lines = []
        elif header_lower.startswith("forensic findings"):
            if current_section:
                sections[current_section] = _join_section(current_lines, current_section)
            current_section = "forensic_findings"
            current_lines = []
        elif header_lower.startswith("evidentiary gaps"):
            if current_section:
                sections[current_section] = _join_section(current_lines, current_section)
            current_section = "evidentiary_gaps"
            current_lines = []
        else:
            current_lines.append(line)

    if current_section:
        sections[current_section] = _join_section(current_lines, current_section)

    # Parse bullet lists into structured data
    findings = []
    if isinstance(sections["forensic_findings"], str):
        for line in sections["forensic_findings"].split("\n"):
            line = line.strip().lstrip("- •*")
            if line:
                findings.append(ForensicObservation(observation=line, severity="MEDIUM"))

    gaps = []
    if isinstance(sections["evidentiary_gaps"], str):
        for line in sections["evidentiary_gaps"].split("\n"):
            line = line.strip().lstrip("- •*")
            if line:
                gaps.append(line)

    # Parse period titles (format: "period_id | title")
    period_titles = {}
    if isinstance(sections["period_titles"], str):
        for line in sections["period_titles"].split("\n"):
            line = line.strip().lstrip("- •*")
            if "|" in line:
                parts = [p.strip() for p in line.split("|", 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    period_titles[parts[0]] = parts[1]

    return CaseDistillation(
        executive_summary=sections["executive_summary"] if isinstance(sections["executive_summary"], str) else "",
        ownership_chain=sections["ownership_chain"] if isinstance(sections["ownership_chain"], str) else "",
        forensic_findings=findings,
        evidentiary_gaps=gaps,
        period_titles=period_titles,
    )
```

Add module-level helper:

```python
def _join_section(lines: list[str], section_name: str) -> str:
    """Join accumulated lines into section content."""
    return "\n".join(lines).strip()
```

Update imports to include `CaseDistillation`.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/narrative/test_generator.py::TestCaseDistillation -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/generator.py tests/narrative/test_generator.py
git commit -m "feat: add _generate_distillation method (Sonnet, once per case)"
```

---

## Task 5: Rewire `generate()` to Use Event Narratives + Distillation

**Files:**
- Modify: `farmer_factory/narrative/generator.py`
- Test: `tests/narrative/test_generator.py`

**Step 1: Write the failing test**

```python
class TestFullGeneration:
    @patch("farmer_factory.narrative.generator.ClaudeAPIClient")
    def test_generate_includes_event_narratives(self, mock_client_cls):
        """Full generation produces event_narratives dict and distillation."""
        mock_client = Mock()
        mock_client_cls.return_value = mock_client
        # Responses: N event narrative calls (haiku) + 1 summary (kept) + 1 distillation (sonnet)
        mock_client.call_standard.return_value = (
            "Title\n---\nNarrative text here.\n---\nOBSERVATIONS:\nSomething | MEDIUM"
        )

        gen = CaseNarrativeGenerator(api_key="test", max_cost=50.0, primary_model="sonnet")
        gen.domain_context = ""

        # Build a minimal mock graph
        mock_graph = Mock()
        mock_graph.graph.nodes = ["doc_1", "ent_1"]
        mock_graph.get_entity.side_effect = lambda nid: {
            "doc_1": {"entity_type": "DOCUMENT", "name": "Escritura", "date": "1955-01-01"},
            "ent_1": {"entity_type": "PERSON", "name": "Mario", "extracted_from": "doc_1"},
        }.get(nid)
        mock_graph.get_relations.return_value = []

        result = gen.generate("TEST", mock_graph)
        assert len(result.event_narratives) > 0
        assert result.distillation is not None
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/narrative/test_generator.py::TestFullGeneration -v`
Expected: FAIL (event_narratives empty or distillation is None)

**Step 3: Rewrite `generate()` method**

The new `generate()` flow:

1. Extract documents, entities, relations (same as before)
2. Group by decade, merge sparse periods (same as before — periods kept for chronological view)
3. **Build events** from relations (CONFISCATED, SOLD, INHERITED) + implicit FILED events (same logic as timeline API)
4. For each event: `_generate_event_narrative()` using Haiku
5. Generate case summary (keep existing `_generate_summary()`)
6. Generate distillation: `_generate_distillation()` using Sonnet
7. Build periods with event references (narrative text = concatenation of event narratives in that period, or null)

Key changes to `generate()`:

```python
def generate(self, case_id: str, graph: KnowledgeGraph) -> CaseNarrative:
    # ... existing steps 1-2 (extract, group) ...

    # Step 3: Build events from relations + implicit FILED
    events = self._build_events(documents, all_entities, all_relations, period_groups)

    # Step 4: Generate event narratives (Haiku, per-event)
    event_narratives: dict[str, EventNarrative] = {}
    for event in events:
        event_docs = [d for d in documents if d["id"] in event["document_ids"]]
        event_entities = [e for e in all_entities if e["id"] in event["entity_ids"]]
        event_relations = self._relations_for_period(event_entities, all_relations)

        en = self._generate_event_narrative(
            event_id=event["id"],
            event_type=event["event_type"],
            event_summary=event["summary"],
            year=event["year"],
            date=event.get("date"),
            documents=event_docs,
            entities=event_entities,
            relations=event_relations,
            parties=event.get("parties", []),
        )
        event_narratives[event["id"]] = en

    # Step 5: Build structural periods (no LLM calls — narrative=null)
    narrative_periods = []
    for period_key, period_docs in sorted(period_groups.items()):
        start_year, end_year = self._parse_period_key(period_key)
        period_entities = self._entities_for_documents(period_docs, all_entities, graph)
        period_relations = self._relations_for_period(period_entities, all_relations)
        highlighted = self._extract_highlighted_events(period_entities, period_relations)
        narrative_periods.append(NarrativePeriod(
            period_id=period_key,
            label=_get_period_label(start_year, end_year),
            title="",
            narrative=None,  # No LLM prose — distillation handles synthesis
            document_ids=[d["id"] for d in period_docs],
            entity_ids=[e["id"] for e in period_entities],
            highlighted_events=highlighted,
            evidence=[],
        ))

    # Step 6: Case summary
    case_summary = self._generate_summary(...)

    # Step 7: Distillation (Sonnet, once) — also generates period titles
    date_range = self._compute_date_range(documents)
    distillation = self._generate_distillation(
        case_id=case_id,
        date_range=date_range,
        total_documents=len(documents),
        narrative_periods=narrative_periods,
        event_narratives=event_narratives,
    )

    # Step 8: Apply LLM-generated period titles from distillation
    for period in narrative_periods:
        if period.period_id in distillation.period_titles:
            period.title = distillation.period_titles[period.period_id]

    return CaseNarrative(
        metadata=metadata,
        case_summary=case_summary,
        periods=narrative_periods,
        event_narratives=event_narratives,
        distillation=distillation,
    )
```

Add `_build_events()` method that mirrors timeline API event construction:

```python
def _build_events(
    self,
    documents: list[dict],
    entities: list[dict],
    relations: list[dict],
    period_groups: dict[str, list[dict]],
) -> list[dict]:
    """Build event list from relations (CONFISCATED/SOLD/INHERITED) + implicit FILED."""
    events = []
    counter = 0

    # Highlighted events from relations
    highlighted_dates = set()
    for rel in relations:
        rel_type = rel.get("relation_type", "")
        if rel_type in ("CONFISCATED", "SOLD", "INHERITED"):
            year = None
            date = rel.get("date")
            if date:
                try:
                    year = int(str(date)[:4])
                except (ValueError, TypeError):
                    pass
            if year is None:
                continue

            highlighted_dates.add(date)
            events.append({
                "id": f"evt_{counter}",
                "event_type": rel_type,
                "year": year,
                "date": date,
                "summary": f"{rel.get('source_name', '?')} {rel_type.lower()} {rel.get('target_name', '?')}",
                "parties": [rel.get("source_name", "Unknown"), rel.get("target_name", "Unknown")],
                "document_ids": [d["id"] for d in documents if d.get("date") and str(d["date"])[:4] == str(year)],
                "entity_ids": [rel.get("source"), rel.get("target")],
            })
            counter += 1

    # Implicit FILED events for documents not covered
    for doc in documents:
        date = doc.get("date")
        if not date or date in highlighted_dates:
            continue
        try:
            year = int(str(date)[:4])
        except (ValueError, TypeError):
            continue
        events.append({
            "id": f"evt_{counter}",
            "event_type": "FILED",
            "year": year,
            "date": date,
            "summary": f"{doc.get('name', doc['id'])} entered the record",
            "parties": [],
            "document_ids": [doc["id"]],
            "entity_ids": [],
        })
        counter += 1

    events.sort(key=lambda e: (e["year"], e.get("date") or ""))
    return events
```

**Step 4: Run all tests**

Run: `python3 -m pytest tests/narrative/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/generator.py tests/narrative/test_generator.py
git commit -m "feat: rewire generate() to produce event narratives + distillation"
```

---

## Task 6: Update Timeline API — Serve Event Narratives

**Files:**
- Modify: `farmer_vault/app/api/cases/[caseId]/timeline/route.ts`

**Step 1: Update `TimelineEvent` interface and response**

Add fields to `TimelineEvent`:

```typescript
interface TimelineEvent {
  id: string;
  year: number;
  date: string | null;
  eventType: 'CONFISCATED' | 'SOLD' | 'INHERITED' | 'FILED';
  summary: string;
  parties: string[];
  documentIds: string[];
  entityIds: string[];
  periodId: string;
  // New: from event_narratives
  narrative?: string | null;
  title?: string | null;
  forensicObservations?: Array<{ observation: string; severity: string }>;
  inlineEntities?: Array<{ name: string; entityId: string; entityType: string; verificationTier: string }>;
}
```

Add `CaseNarrativeData` update to include:

```typescript
interface CaseNarrativeData {
  // ... existing fields ...
  event_narratives?: Record<string, {
    event_id: string;
    event_type: string;
    year: number;
    date?: string | null;
    title: string;
    summary: string;
    narrative: string;
    document_ids: string[];
    entity_ids: string[];
    parties: string[];
    forensic_observations?: Array<{ observation: string; severity: string }>;
    inline_entities?: Array<{ name: string; entity_id: string; entity_type: string }>;
  }>;
  distillation?: {
    executive_summary: string;
    ownership_chain: string;
    forensic_findings: Array<{ observation: string; severity: string }>;
    evidentiary_gaps: string[];
    cross_event_patterns: string[];
  } | null;
}
```

In the event construction loop, match events to `event_narratives` by matching event_type + year + summary (since event IDs are generated independently):

```typescript
// After building events, enrich with narratives
const eventNarratives = caseNarrative?.event_narratives || {};
for (const event of events) {
  // Try to match by event_id first, then by type+year
  const en = eventNarratives[event.id]
    || Object.values(eventNarratives).find(
      n => n.event_type === event.eventType && n.year === event.year
    );
  if (en) {
    event.narrative = en.narrative;
    event.title = en.title;
    event.forensicObservations = (en.forensic_observations || []).map(o => ({
      observation: o.observation,
      severity: o.severity,
    }));
    // Resolve inline entities against graph nodes
    event.inlineEntities = (en.inline_entities || []).map(ie => {
      const node = graphData.nodes.find(n => n.id === ie.entity_id);
      return {
        name: ie.name,
        entityId: ie.entity_id,
        entityType: ie.entity_type,
        verificationTier: node?.verification?.tier || 'TIER_3_AI',
      };
    });
  }
}
```

Apply distillation period titles to periods:

```typescript
// Override period titles with LLM-generated ones from distillation
const periodTitles = caseNarrative?.distillation?.period_titles || {};
for (const period of periods) {
  if (periodTitles[period.id]) {
    period.title = periodTitles[period.id];
  }
}
```

Add `distillation` to the response:

```typescript
return NextResponse.json({
  periods,
  events,
  gaps,
  totalDocuments: documents.length,
  dateRange: graphData.metadata.date_range,
  caseSummary: caseNarrative?.case_summary || null,
  distillation: caseNarrative?.distillation || null,
});
```

**Step 2: Verify build**

Run: `npm run build`
Expected: No TypeScript errors

**Step 3: Commit**

```bash
git add app/api/cases/[caseId]/timeline/route.ts
git commit -m "feat: serve event narratives and distillation from timeline API"
```

---

## Task 7: Add ScrollPeriodHeadline + Update ScrollTimeline Layout

**Files:**
- Create: `farmer_vault/components/Timeline/ScrollPeriodHeadline.tsx`
- Modify: `farmer_vault/components/Timeline/ScrollTimeline.tsx`
- Modify: `farmer_vault/components/Timeline/index.ts`

**Step 1: Create `ScrollPeriodHeadline.tsx`**

A visual section divider on the spine — the period label as a sticky-ish headline that introduces a group of events.

```tsx
'use client';

interface ScrollPeriodHeadlineProps {
  label: string;
  dateRange: string;
  documentCount: number;
  entityCount: number;
}

export default function ScrollPeriodHeadline({ label, dateRange, documentCount, entityCount }: ScrollPeriodHeadlineProps) {
  return (
    <div className="relative min-h-[30vh] flex items-center pl-16 pr-8">
      {/* Spine marker — wider bar instead of dot */}
      <div className="absolute left-[19px] top-1/2 -translate-y-1/2 w-5 h-[2px] bg-slate-600" />

      <div className="max-w-2xl w-full py-8">
        <time className="block text-xs font-mono tabular-nums text-slate-600 tracking-widest uppercase mb-1">
          {dateRange}
        </time>
        <h2 className="text-2xl font-display tracking-tight text-slate-300">
          {label}
        </h2>
        <p className="text-xs text-slate-600 font-mono mt-1">
          {documentCount} document{documentCount !== 1 ? 's' : ''} &middot; {entityCount} entit{entityCount !== 1 ? 'ies' : 'y'}
        </p>
      </div>
    </div>
  );
}
```

**Step 2: Update `ScrollTimeline.tsx` to render period-first layout**

Instead of flat events + gaps, render:
```
for each period (sorted chronologically):
  <ScrollPeriodHeadline />
  for each event in period (sorted by year):
    <ScrollEventNode />
    (gaps between events)
```

The timeline API response already has `periods` and `events` with `periodId`. Group events by `periodId`:

```tsx
// Group events by periodId
const eventsByPeriod = new Map<string, ScrollEventData[]>();
for (const event of events) {
  const list = eventsByPeriod.get(event.periodId) || [];
  list.push(event);
  eventsByPeriod.set(event.periodId, list);
}

// Render period-first
{periods.map(period => (
  <React.Fragment key={period.id}>
    <ScrollPeriodHeadline
      label={period.title}
      dateRange={period.dateRange}
      documentCount={period.documentCount}
      entityCount={period.entityCount}
    />
    {(eventsByPeriod.get(period.id) || []).map(event => (
      <ScrollEventNode key={event.id} event={event} caseId={caseId} />
    ))}
  </React.Fragment>
))}
```

The `ScrollTimeline` component needs `periods` prop added alongside `events` and `gaps`.

**Step 3: Export from index.ts**

Add `ScrollPeriodHeadline` to `components/Timeline/index.ts`.

**Step 4: Update `narrative/page.tsx` to pass periods to `ScrollTimeline`**

```tsx
<ScrollTimeline
  events={data.events || []}
  periods={data.periods || []}
  gaps={data.gaps || []}
  caseId={caseId}
/>
```

**Step 5: Verify build**

Run: `npm run build`

**Step 6: Commit**

```bash
git add components/Timeline/ScrollPeriodHeadline.tsx components/Timeline/ScrollTimeline.tsx components/Timeline/index.ts app/case/[caseId]/narrative/page.tsx
git commit -m "feat: add period headlines to scroll timeline layout"
```

---

## Task 8: Update ScrollEventNode — Display Event Narrative

**Files:**
- Modify: `farmer_vault/components/Timeline/ScrollEventNode.tsx`

**Step 1: Update `ScrollEventData` interface**

Add fields already declared but now populated:

```typescript
export interface ScrollEventData {
  // ... existing fields ...
  title?: string | null;
  inlineEntities?: Array<{ name: string; entityId: string; entityType: string; verificationTier: string }>;
}
```

**Step 2: Update rendering**

At Level 2, if `event.title` exists, show it above the summary. Use first 2 sentences of `event.narrative` (already happening) for the snippet. At Level 3, the "Explore this event" link already exists — no change needed.

**Step 3: Verify build**

Run: `npm run build`
Expected: No TypeScript errors

**Step 4: Commit**

```bash
git add components/Timeline/ScrollEventNode.tsx
git commit -m "feat: display event title and narrative in scroll nodes"
```

---

## Task 9: Update Event Detail Page — Rich Event Narrative

**Files:**
- Modify: `farmer_vault/app/case/[caseId]/narrative/event/[eventId]/page.tsx`

**Step 1: Replace period narrative with event narrative**

The event detail page currently shows `period.narrative`. Change it to show:
1. The event's own `title` as the h1 (instead of `event.summary`)
2. The event's own `narrative` (from `event.narrative`) rendered with inline entity links
3. The event's own `forensicObservations` rendered as cyan callouts
4. Keep entities and documents sections as-is

Key changes:

```tsx
// Replace h1 with event title if available
<h1 className="text-2xl font-display tracking-tight text-slate-100 mb-2">
  {event.title || event.summary}
</h1>

// Replace "Period Narrative" section with "Event Narrative"
{event.narrative && (
  <section className="mb-8">
    <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
      Event Narrative
    </h2>
    <div className="dossier-prose">
      {event.narrative.split('\n\n').map((paragraph: string, i: number) => (
        <p key={i}>
          {renderNarrativeWithEntities(paragraph, event.inlineEntities || inlineEntities, caseId)}
        </p>
      ))}
    </div>
  </section>
)}

// Add forensic observations if present
{event.forensicObservations?.length > 0 && (
  <section className="mb-8">
    <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
      Forensic Observations
    </h2>
    <div className="space-y-2">
      {event.forensicObservations.map((obs: any, i: number) => (
        <div key={i} className="flex items-start gap-2 px-3 py-2 rounded text-sm bg-cyan-500/5 border border-cyan-500/15">
          <span className="shrink-0 text-cyan-400">◆</span>
          <span className="text-slate-300">{obs.observation}</span>
          <span className="ml-auto shrink-0 font-mono text-xs text-cyan-500/60">{obs.severity}</span>
        </div>
      ))}
    </div>
  </section>
)}
```

**Step 2: Verify build**

Run: `npm run build`
Expected: No TypeScript errors

**Step 3: Commit**

```bash
git add app/case/[caseId]/narrative/event/[eventId]/page.tsx
git commit -m "feat: display event-specific narrative on event detail page"
```

---

## Task 10: Update Narrative Page — Remove Period Narrative Enrichment

**Files:**
- Modify: `farmer_vault/app/case/[caseId]/narrative/page.tsx`

**Step 1: Remove period-to-event narrative mapping**

The current page enriches events with period narratives:
```tsx
const periodMap = new Map<string, string>();
// ...
narrative: periodMap.get(e.periodId as string) || null,
```

This is no longer needed — the API now returns `narrative` directly on each event. Remove the enrichment logic:

```tsx
const enrichedEvents = data.events || [];
```

**Step 2: Verify build**

Run: `npm run build`

**Step 3: Commit**

```bash
git add app/case/[caseId]/narrative/page.tsx
git commit -m "refactor: remove period-to-event narrative mapping (API serves event narratives directly)"
```

---

## Task 11: Case Distillation Page + Sidebar Sub-Tab

**Files:**
- Create: `farmer_vault/app/case/[caseId]/narrative/distillation/page.tsx`
- Modify: `farmer_vault/components/shared/Sidebar.tsx`

**Step 1: Create distillation page**

```tsx
import Link from 'next/link';

interface DistillationPageProps {
  params: Promise<{ caseId: string }>;
}

async function getTimeline(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/timeline`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch timeline');
  return res.json();
}

export default async function DistillationPage({ params }: DistillationPageProps) {
  const { caseId } = await params;

  try {
    const data = await getTimeline(caseId);
    const distillation = data.distillation;

    if (!distillation) {
      return (
        <div className="p-8">
          <div className="max-w-4xl mx-auto">
            <header className="mb-8">
              <h1 className="text-4xl font-display tracking-tight text-slate-50">Case Distillation</h1>
              <hr className="dossier-rule mt-4 mb-2" />
            </header>
            <div className="p-8 bg-slate-900 border border-slate-800 rounded text-center">
              <p className="text-slate-500 font-mono text-sm">
                Case distillation not yet generated. Run the narrative pipeline to produce this report.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <header className="mb-8">
            <h1 className="text-4xl font-display tracking-tight text-slate-50">Case Distillation</h1>
            <p className="text-sm text-slate-500 mt-2 font-mono">
              Forensic intelligence report — cross-event analysis
            </p>
            <hr className="dossier-rule mt-4 mb-2" />
          </header>

          {/* AI Disclaimer */}
          <div className="mb-8 px-4 py-2 bg-amber-500/5 border border-amber-500/15 rounded">
            <p className="text-xs text-amber-500/70 italic">
              AI-generated forensic intelligence — not a legal document. All inferences are TIER_3_AI.
            </p>
          </div>

          {/* Executive Summary */}
          <section className="mb-10">
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
              Executive Summary
            </h2>
            <div className="dossier-prose">
              {distillation.executive_summary.split('\n\n').map((p: string, i: number) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {/* Chain of Custody */}
          <section className="mb-10">
            <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
              Chain of Custody
            </h2>
            <div className="dossier-prose">
              {distillation.ownership_chain.split('\n\n').map((p: string, i: number) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>

          {/* Forensic Findings */}
          {distillation.forensic_findings?.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
                Forensic Findings ({distillation.forensic_findings.length})
              </h2>
              <div className="space-y-2">
                {distillation.forensic_findings.map((f: any, i: number) => (
                  <div key={i} className="flex items-start gap-2 px-3 py-2 rounded text-sm bg-cyan-500/5 border border-cyan-500/15">
                    <span className="shrink-0 text-cyan-400">◆</span>
                    <span className="text-slate-300">{f.observation}</span>
                    <span className="ml-auto shrink-0 font-mono text-xs text-cyan-500/60">{f.severity}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Evidentiary Gaps */}
          {distillation.evidentiary_gaps?.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
                Evidentiary Gaps ({distillation.evidentiary_gaps.length})
              </h2>
              <div className="space-y-2">
                {distillation.evidentiary_gaps.map((gap: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 px-3 py-2 rounded text-sm bg-amber-500/5 border border-amber-500/15">
                    <span className="shrink-0 text-amber-400">△</span>
                    <span className="text-slate-300">{gap}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    );
  } catch {
    return (
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          <div className="p-8 bg-slate-900 border border-red-800/50 rounded text-center">
            <p className="text-red-400 font-mono text-sm">Failed to load distillation data</p>
          </div>
        </div>
      </div>
    );
  }
}
```

**Step 2: Add "Distillation" to sidebar sub-items**

In `Sidebar.tsx`, add to `SUB_ITEMS`:

```typescript
const SUB_ITEMS = [
  { label: 'Chronological', href: 'chronological' },
  { label: 'Distillation', href: 'distillation' },
  { label: 'Geolocation', href: 'geolocation' },
  { label: 'Graph', href: 'graph' },
];
```

**Step 3: Verify build**

Run: `npm run build`

**Step 4: Commit**

```bash
git add app/case/[caseId]/narrative/distillation/page.tsx components/shared/Sidebar.tsx
git commit -m "feat: add Case Distillation page and sidebar sub-tab"
```

---

## Task 12: Run All Tests + Build Verification

**Step 1: Run Python tests**

Run: `python3 -m pytest tests/narrative/ -v`
Expected: ALL PASS

**Step 2: Run TypeScript build**

Run: `npm run build`
Expected: No errors

**Step 3: Commit any remaining fixes**

---

## Task 13: Update Documentation

**Files:**
- Modify: `.claude/CLAUDE.md`
- Modify: `.claude/ROADMAP.md`

Update both files to document Phase 9F — Event Narratives + Case Distillation:
- Event narrative generation (Haiku, per-event)
- Case distillation (Sonnet, once per case)
- New sidebar sub-tab: Distillation
- Cost model change (~60-80% reduction)
- New models: EventNarrative, CaseDistillation
- Updated CaseNarrative schema (event_narratives dict, distillation field)

**Commit:**

```bash
git add -f .claude/CLAUDE.md .claude/ROADMAP.md
git commit -m "docs: document Phase 9F event narratives + case distillation"
```

---

## Verification Checklist

1. `python3 -m pytest tests/narrative/ -v` — all pass
2. `npm run build` — no TypeScript errors
3. `/case/TEST-CERESA/narrative` — scroll experience shows event narratives (if `case_narrative.json` has `event_narratives`)
4. Click "Explore this event" — event detail page shows event-specific narrative (not period narrative)
5. Sidebar: Distillation sub-tab visible under AI Analysis
6. `/case/TEST-CERESA/narrative/distillation` — shows forensic intelligence report (if `distillation` present in JSON)
7. Chronological view still works at `/narrative/chronological`
