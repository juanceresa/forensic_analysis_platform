# Contextual Narrative Generation - Design Document

> **Created:** 2026-01-25
> **Status:** Design Complete - Ready for Implementation
> **Phase:** Post-MVP1 Feature

---

## Overview

User-driven contextual narrative generation for knowledge graph entities. When users click on any entity (person, property, location, organization), the system analyzes the local graph context and generates a forensic intelligence narrative with full evidence citations.

**Key insight:** Properties like "Villa Aurelia" are often the "main character" in restitution stories, even if the user clicked on a peripheral entity. The system auto-identifies the optimal narrative focal point within each constellation.

---

## Goals

1. **Help families understand complex property histories** through accessible narratives
2. **Maintain forensic rigor** with inline citations and verification tiers
3. **Optimize costs** by matching model complexity to entity complexity
4. **Keep narratives current** with session-scoped caching that invalidates on graph updates

---

## User Experience

### Interaction Flow

1. **User clicks any node** → System highlights entire connected component (constellation)
2. **User navigates** within constellation (selector moves between highlighted nodes)
3. **User clicks "Generate Story"** → System:
   - Identifies optimal hub entity using story centrality scoring
   - Analyzes local graph context
   - Selects model (Haiku or Sonnet) based on complexity
   - Generates narrative with inline citations
4. **Display:** Hybrid format with chronological narrative + evidence sidebar

### Example Output

**Main Narrative Panel:**
```
Villa Aurelia first appears in records in 1952 when Mario Ceresa
acquired the property [①]. The property transferred to Juan Ceresa
in 1956 for 50,000 pesos [②]. In 1962, the property was confiscated
by the state with no record of compensation [③].
```

**Evidence Sidebar:**
```
[①] Original Acquisition (1952)
    Doc 3, p.2 - TIER_2_ANALYST (0.92)
    "Mario Ceresa, propietario de Villa Aurelia"

[②] Transfer to Juan Ceresa (1956)
    Primary: Doc 7, p.1 - TIER_2_ANALYST (0.89) - "1956"
    Conflict: Doc 3, p.2 - TIER_3_AI (0.61) - "1957"
    ⚠️ Using highest confidence version

[③] Confiscation (1962)
    Doc 12, p.3 - TIER_3_AI (0.74)
    "confiscada por el estado en 1962"
```

---

## Architecture

### Module Structure

**New module:** `farmer_factory/narrative/`

```
narrative/
├── __init__.py
├── generator.py          # Narrative generation orchestrator
├── constellation.py      # Graph analysis and hub identification
├── scorer.py            # Story centrality scoring algorithm
├── cache.py             # Session-scoped caching with invalidation
├── models.py            # Pydantic models for narrative output
└── prompts.py           # Claude prompts for narrative generation
```

### Key Components

**1. Constellation Analysis (`constellation.py`)**
- Extract connected component from clicked node
- Calculate story centrality scores for all entities in constellation
- Identify optimal narrative focal point

**2. Story Centrality Scoring (`scorer.py`)**

Adapts PageRank for forensic narratives:

```python
def calculate_story_centrality(entity, constellation, graph):
    # Base score by entity type (properties as protagonists)
    type_weights = {
        'PROPERTY': 10.0,
        'LOCATION': 8.0,
        'PERSON': 5.0,
        'ORGANIZATION': 3.0
    }
    base_score = type_weights[entity.entity_type]

    # Connection count (network importance)
    connection_score = len(graph.get_neighbors(entity.id)) * 2.0

    # Document frequency (corroboration strength)
    document_score = len(entity.extracted_from) * 3.0

    # Weighted relations (some matter more than others)
    relation_weights = {
        'OWNS': 3.0,
        'SOLD': 2.5,
        'INHERITED': 2.5,
        'CONFISCATED': 2.5,
        'LOCATED_IN': 1.5,
        'WITNESSED': 1.0,
        'EMPLOYED_BY': 1.0
    }
    weighted_relations = sum(
        relation_weights.get(rel.relation_type, 1.0)
        for rel in graph.get_relations_for_entity(entity.id)
    )

    return base_score + connection_score + document_score + weighted_relations
```

**3. Narrative Generator (`generator.py`)**

Two-stage generation process:

**Stage 1: Extract Structured Facts**
- Parse graph into factual claims
- Each claim backed by document evidence
- Identify conflicts (competing claims)

**Stage 2: Generate Narrative**
- Write chronological story from verified facts
- Inline citations for every claim
- Present highest-confidence version, conflicts in sidebar

**4. Session Cache (`cache.py`)**

Session-scoped caching with graph-state invalidation:

```python
cache_key = f"narrative:{session_id}:{focal_entity_id}:{graph_hash}"

# graph_hash includes:
# - Entity verification tiers (TIER_3_AI vs TIER_2_ANALYST)
# - Constellation membership
# - Relation count

# Cache invalidates when:
# - Analyst verifies entities (tier change)
# - New entities added to constellation
# - Relations modified
```

**Benefits:**
- Same user, same entity → cached (no cost)
- Analyst verifies data → hash changes, regenerates
- Session expires after 1 hour
- Tracks API cost per session ($5 limit)

---

## Data Models

### Narrative Output Schema

```python
class EvidenceCitation(BaseModel):
    """Single piece of evidence supporting a claim."""
    doc_id: str
    page: Optional[int] = None
    quote: str
    confidence: float
    verification_tier: VerificationTier
    ocr_confidence: Optional[float] = None

class ConflictingClaim(BaseModel):
    """Competing versions of a fact."""
    claim_summary: str  # "Sale date"
    versions: List[EvidenceCitation]
    resolution: str  # "Using highest confidence"
    citation_number: int

class FactualClaim(BaseModel):
    """Single fact in the narrative."""
    claim_text: str
    citation_number: int
    evidence: List[EvidenceCitation]
    temporal_context: Optional[str] = None
    fact_type: Optional[str] = None

class NarrativeResult(BaseModel):
    """Complete narrative generation result."""
    # Metadata
    focal_entity_id: str
    focal_entity_name: str
    focal_entity_type: str
    constellation_size: int
    generated_at: datetime
    model_used: Literal["haiku", "sonnet"]

    # Content
    main_narrative: str  # Chronological story with [①] citations
    facts: List[FactualClaim]
    conflicts: List[ConflictingClaim]

    # Quality indicators
    total_documents: int
    total_citations: int
    date_range: Optional[str]
    confidence_summary: dict  # {"TIER_3_AI": 12, "TIER_2_ANALYST": 8}
```

---

## Model Selection Logic

**Complexity Score:**

```python
complexity = (
    len(constellation) * 2 +           # Entity count
    len(relations) * 1.5 +             # Relation count
    len(unique_documents) * 3          # Document diversity
)

if complexity > 50:
    model = "sonnet"  # Deep analysis needed
else:
    model = "haiku"   # Simple context
```

**Estimates for TEST-CERESA:**
- Villa Aurelia (15 connections, 8 docs): complexity ~80 → Sonnet
- Minor witness (2 connections, 1 doc): complexity ~12 → Haiku
- ~72% of entities use Haiku, ~28% use Sonnet

---

## API Design

### Backend Endpoint

```
POST /api/cases/{caseId}/narrative

Request:
{
  "clicked_node_id": "prop_villa_aurelia_001",
  "constellation_ids": ["prop_001", "person_mario_001", ...],
  "max_depth": 3  // Optional analysis depth
}

Response:
{
  "focal_entity_id": "prop_villa_aurelia_001",
  "focal_entity_name": "Villa Aurelia",
  "main_narrative": "Villa Aurelia first appears...",
  "facts": [
    {
      "claim_text": "Mario Ceresa owned Villa Aurelia in 1952",
      "citation_number": 1,
      "evidence": [...]
    }
  ],
  "conflicts": [...],
  "model_used": "sonnet",
  "from_cache": false,
  "session_cost": 0.15
}
```

### Frontend Integration

```typescript
// farmer_vault/components/KnowledgeGraph.tsx
const onNodeClick = (nodeId: string) => {
  // 1. Highlight constellation
  const constellation = findConnectedComponent(nodeId)
  highlightNodes(constellation)

  // 2. Show narrative panel
  setNarrativePanel({
    visible: true,
    clickedNode: nodeId,
    constellation: constellation
  })
}

const generateNarrative = async () => {
  const response = await fetch(`/api/cases/${caseId}/narrative`, {
    method: 'POST',
    body: JSON.stringify({
      clicked_node_id: selectedNode,
      constellation_ids: constellation.map(n => n.id)
    })
  })

  const narrative = await response.json()
  displayNarrative(narrative)
}
```

---

## Error Handling

### Edge Cases

**1. Insufficient Data (< 3 entities)**
```python
if len(constellation) < 3:
    return SimpleNarrative(
        text=f"{entity.name} appears in {len(docs)} document(s). "
             "Limited context for narrative.",
        skip_ai_generation=True
    )
```

**2. All Low-Confidence Evidence**
```python
if avg_confidence < 0.7 and all_tier_3:
    return NarrativeResult(
        narrative="...",
        quality_warning="Based entirely on unverified AI extraction. "
                       "Analyst review recommended.",
        show_warning_banner=True
    )
```

**3. API Failures**
```python
try:
    narrative = api_client.call_with_retry(prompt, max_retries=3)
except Exception as e:
    return FallbackNarrative(
        text="Unable to generate narrative. View individual facts below.",
        show_raw_facts=True
    )
```

**4. Circular Logic Detected**
```python
if detect_circular_ownership(facts):
    return NarrativeResult(
        narrative="...",
        data_quality_issues=["Circular ownership - manual review required"],
        analyst_flag=True
    )
```

**5. Too Complex (>100 entities)**
```python
if constellation_size > 100:
    return {
        "error": "Constellation too large",
        "suggestion": "Click a more specific entity",
        "size": constellation_size
    }
```

---

## Cost Estimation

### Per-Case Worst Case (TEST-CERESA)

```
Total entities: 207

Distribution:
- Simple (≤3 connections): 150 entities → Haiku
- Complex (>3 connections): 57 entities → Sonnet

Token usage:
- Haiku: 150 × 2000 tokens = 300K tokens
- Sonnet: 57 × 3000 tokens = 171K tokens

Cost (Anthropic 2026 pricing):
- Haiku: 300K × $0.25/M = $0.08
- Sonnet: 171K × $3.00/M = $0.51

Total worst case: $0.59 per full exploration
Realistic per session: $0.10 - $0.20
```

### Cost Controls

1. **Session limits:** $5 per session max
2. **Cache hits:** 0 cost for repeated clicks
3. **Model selection:** 72% use cheaper Haiku
4. **Lazy generation:** Only generate on user request

---

## Testing Strategy

### Unit Tests

```python
# Hub identification
def test_story_centrality_prefers_properties()
def test_hub_identification_with_ties()

# Narrative quality
def test_narrative_includes_all_citations()
def test_conflict_resolution_picks_highest_confidence()

# Caching
def test_cache_hit_same_session()
def test_cache_invalidation_on_verification()
```

### Integration Tests

```python
# End-to-end with real case
def test_villa_aurelia_narrative_generation()
def test_simple_entity_uses_haiku()
def test_session_cost_tracking()
```

### Performance Benchmarks

**Target SLAs:**
- Simple entity (≤3 connections): <3 seconds, Haiku
- Medium entity (4-10 connections): <8 seconds, Sonnet
- Complex hub (>10 connections): <15 seconds, Sonnet
- Cache hit: <100ms

---

## Rollout Plan

### Phase 1: Soft Launch (1-2 analysts)
- Enable on TEST-CERESA only
- Manual testing with known entities
- Collect feedback on narrative quality and citation accuracy

### Phase 2: Limited Rollout (All analysts)
- Enable for all cases
- Cost monitoring per session
- A/B test Haiku vs Sonnet threshold tuning

### Phase 3: Family Access
- Enable for family members (read-only)
- Add "Request Regeneration" button (analyst approval required)
- Usage analytics (which entities explored most)

---

## Future Enhancements

### Post-MVP Improvements

1. **Comparative Narratives**
   - "Compare Villa Aurelia to other Ceresa properties"
   - Side-by-side ownership timelines

2. **Export to PDF Dossier**
   - Generate formatted PDF report
   - Include narrative + full evidence citations
   - Suitable for legal submission

3. **Multi-Focal Narratives**
   - Tell story from multiple perspectives
   - "Villa Aurelia's history from the Ceresa family perspective"
   - "Villa Aurelia's history from the state perspective"

4. **Temporal Analysis**
   - "What happened to the Ceresa properties in 1962?"
   - Cross-entity timeline generation

5. **Gap Highlighting**
   - "Missing ownership records 1956-1962"
   - Suggested research directions

---

## Security & Privacy

### Access Control

- **Narratives inherit case-level permissions**
- Generated narratives include case_id
- Supabase RLS enforces same access rules as graph data

### Audit Logging

```python
logger.info(
    "Narrative generated",
    extra={
        "user_id": user_id,
        "session_id": session_id,
        "case_id": case_id,
        "focal_entity": hub_entity.id,
        "model_used": model,
        "cost_estimate": cost,
        "from_cache": from_cache
    }
)
```

### Data Retention

- Narratives cached in Redis (1-hour TTL)
- Not persisted to database
- Regenerated fresh each session
- No PII in cache keys

---

## Legal Compliance

### Forensic Facts Only

Prompts explicitly constrain Claude:
- "Only extract claims directly supported by document quotes"
- "Never infer or make legal conclusions"
- "Use past tense, factual tone only"

### Verification Transparency

Every claim shows:
- Source document and page
- Verification tier (TIER_3_AI vs TIER_2_ANALYST)
- Confidence score
- OCR quality indicator

### Disclaimer

Narratives include prominent disclaimer:
> "This narrative presents facts documented in source materials. It does not constitute legal advice or proof of ownership. Consult legal counsel for case strategy."

---

## Success Metrics

### Quality Metrics
- Citation accuracy: 100% (every claim has evidence)
- Conflict detection rate: >90% of known conflicts surfaced
- Analyst approval rate: >80% narratives approved without edits

### Usage Metrics
- Narratives generated per session
- Cache hit rate (target: >60%)
- Cost per session (target: <$0.25)
- Entities explored (which get most attention)

### Performance Metrics
- P50 generation time: <5 seconds
- P95 generation time: <12 seconds
- API error rate: <1%

---

## Implementation Checklist

- [ ] Create `farmer_factory/narrative/` module
- [ ] Implement story centrality scoring (`scorer.py`)
- [ ] Build constellation analysis (`constellation.py`)
- [ ] Write narrative generation prompts (`prompts.py`)
- [ ] Implement two-stage generator (`generator.py`)
- [ ] Build session cache with Redis (`cache.py`)
- [ ] Create Pydantic models (`models.py`)
- [ ] Add backend API endpoint (`/api/cases/[id]/narrative`)
- [ ] Build frontend narrative panel UI
- [ ] Implement graph visualization highlighting
- [ ] Add evidence sidebar component
- [ ] Write unit tests (scorer, generator, cache)
- [ ] Write integration tests (end-to-end)
- [ ] Cost monitoring dashboard
- [ ] Deploy to staging for analyst testing
- [ ] Collect feedback and iterate
- [ ] Production rollout

---

## Open Questions

1. **Should we pre-generate narratives for known hubs?**
   - Pro: Instant display for important entities
   - Con: Wastes tokens if never viewed, staleness risk

2. **Should conflicts pause generation pending analyst review?**
   - Current: Present both versions, flag in sidebar
   - Alternative: Queue for review before showing narrative

3. **How to handle multi-language narratives?**
   - Documents in Spanish, narrative in English?
   - Preserve original quotes in Spanish?

---

*This design is ready for implementation. See ROADMAP.md for phase scheduling.*
