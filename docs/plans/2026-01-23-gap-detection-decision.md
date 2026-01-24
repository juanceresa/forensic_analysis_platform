# Architectural Decision: Gap Detection Deferred to Analyst Workflow

> **Document Type:** Architectural Decision Record (ADR)
> **Date:** 2026-01-23
> **Status:** ACCEPTED
> **Scope:** Phase 5 (Graph Construction)

---

## Context

The ROADMAP.md Phase 5 includes Task 5.3: Gap Detector - a system to identify:
- Missing ownership links in property chains
- Temporal gaps (e.g., property owned in 1920, then 1960, but no records 1920-1960)
- Orphan entities (entities with no connections to the graph)
- Conflicting claims requiring resolution

Initial plan was to build this as part of the core graph construction pipeline and display gaps in the family-facing Vault UI.

## Problem

Gap detection provides limited value to end-user families:

1. **Cannot Act on Gaps** - If Cuban archives are destroyed or inaccessible, families cannot fill the gaps
2. **Negative Experience** - Highlighting missing data feels like pointing out what families don't have
3. **Wrong Tone** - "You're missing X, Y, Z" undermines the value of what they DO have
4. **Legal Posture** - We deliver "Forensic Facts" not "Case Assessments" - gap analysis feels like the latter

However, gap detection has significant value for **Civic Table analysts**:

1. **Quality Control** - Detects extraction errors (LLM missed a property transfer that IS in the docs)
2. **Research Direction** - Helps analysts know where to dig deeper in available documents
3. **Case Assessment** - Internal tool for scoping work ("this case is 40% complete vs 80% complete")
4. **Pricing Tool** - Helps estimate research effort for case intake

## Decision

**DEFER gap detection from MVP1 (Phase 5) to a future analyst-only workflow.**

Specifically:
- **Remove** Task 5.3 from Phase 5 critical path
- **Do not** display gaps in family-facing Vault UI
- **Add** to future analyst dashboard (post-MVP1) as internal intelligence tool
- **Preserve** simple orphan detection as quality control (entities with zero connections likely indicate extraction errors)

## Rationale

### User Experience Priority

Families come to Civic Table with what they have - often incomplete, degraded documents salvaged from exile. The platform should:
- **Celebrate what exists** rather than mourn what's missing
- **Present facts clearly** without editorial on completeness
- **Enable understanding** of the documents they possess

Gap detection shown to families violates this principle.

### Analyst Value Preserved

Gap detection remains valuable for Civic Table operations:
- **Internal workflow tool** for case management
- **Quality assurance** to catch extraction failures
- **Research planning** to guide document acquisition efforts
- **Delivered contextually** by analysts in human terms, not raw data dumps

### Delivery Method Matters

The same information can be delivered differently:

**Bad (raw gap detection):**
> "Your ownership chain has 3 critical gaps between 1920-1960"

**Good (analyst-mediated insight):**
> "Based on the documents you have, we can trace ownership from 1916-1920 and 1960-1961. If you have any records from the 1920-1960 period, those would help strengthen the chain."

Analysts can deliver gap insights in human, empathetic terms when appropriate.

## Consequences

### Positive
- ✅ Faster MVP1 delivery (Phase 5 complete without Task 5.3)
- ✅ Better family experience (focus on what they have)
- ✅ Appropriate legal posture (facts, not case assessment)
- ✅ Analyst value preserved for future implementation

### Negative
- ⚠️ Delayed internal tooling for analysts (can use manual review initially)
- ⚠️ No automated quality checks for orphan entities (can be added in Phase 6 as part of export validation)

### Neutral
- 📍 Gap detection implementation deferred, not cancelled
- 📍 Will be built as analyst dashboard feature (post-MVP1)
- 📍 May inform pricing/scoping for future cases

## Implementation Notes

### What Changes in Phase 5

**Remove from critical path:**
- Task 5.3: `structure/gap_detector.py` module
- Gap detection in GraphBuilder
- Gap metadata in graph_data.json export

**Keep as quality control:**
- Simple orphan detection (can be part of export validation in Phase 6)
- Entity/relation count stats in metadata
- Existing deduplication and conflict resolution

### Future Implementation (Post-MVP1)

When gap detection is implemented for analysts:

**Analyst Dashboard Features:**
```python
class GapAnalyzer:
    """Internal tool for analyst workflow - NOT exposed to families."""

    def analyze_ownership_chains(self, graph: KnowledgeGraph) -> List[OwnershipGap]:
        """Find missing links in property ownership chains."""
        pass

    def detect_temporal_gaps(self, graph: KnowledgeGraph) -> List[TemporalGap]:
        """Find suspicious time gaps in event sequences."""
        pass

    def find_orphans(self, graph: KnowledgeGraph) -> List[OrphanEntity]:
        """Find entities with no connections (likely extraction errors)."""
        pass

    def suggest_research_targets(self, gaps: List[Gap]) -> List[ResearchTask]:
        """Convert gaps into actionable research tasks for analysts."""
        pass
```

**Use Cases:**
1. **Quality Assurance** - Analyst reviews orphan entities, finds LLM missed a relation
2. **Case Scoping** - Analyst assesses completeness percentage for pricing
3. **Research Planning** - Analyst identifies which document types to search for in archives
4. **Family Communication** - Analyst translates gap insights into empathetic guidance

**NOT Use Cases:**
- ❌ Automatic display in Vault UI
- ❌ Scoring/grading of case strength
- ❌ Legal conclusions about gaps

## Related Decisions

- **ANALYST_GUIDE.md** - Should document gap detection workflow when implemented
- **ARCHITECTURE.md** - Forensic Facts posture (no legal conclusions)
- **ROADMAP.md** - Phase 5 updated to reflect Task 5.3 deferral

## References

- ROADMAP.md Phase 5, Task 5.3
- ARCHITECTURE.md Section on Legal Posture
- ANALYST_GUIDE.md (analyst workflow documentation)
- Discussion: 2026-01-23 brainstorming session

---

**Status:** This decision is accepted and should be reflected in:
1. ✅ ROADMAP.md - Update Phase 5 to mark Task 5.3 as deferred
2. ✅ ANALYST_GUIDE.md - Add placeholder for future gap detection workflow
3. ✅ Phase 5 implementation - Skip gap_detector.py module
4. ✅ Phase 6 planning - Simple orphan detection in export validation (optional quality check)
