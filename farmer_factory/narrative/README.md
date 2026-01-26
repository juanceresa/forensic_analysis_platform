# Narrative Generation Module

User-driven contextual narrative generation for knowledge graph entities with forensic intelligence narratives, inline citations, and event highlighting.

## Quick Start

```python
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph

# Initialize
generator = NarrativeGenerator(api_key="your_anthropic_key")

# Load graph
graph = KnowledgeGraph.load("cases/TEST-CERESA/output/graph_data.json")

# Generate narrative
result = generator.generate(
    clicked_node_id="prop_villa_aurelia_001",
    graph=graph,
    session_id="user_session_123"
)

print(result.main_narrative)
print(f"Cost: ${result.generation_cost:.4f}")
print(f"Highlighted events: {len(result.highlighted_events)}")
```

## Architecture

### Single-Stage LLM Generation
- One API call generates complete narrative with inline citations
- 50% faster and cheaper than two-stage approach
- Narrative voice with forensic rigor

### Story Centrality Scoring
Properties score highest (optimal focal points for restitution):
- PROPERTY: 10.0 base weight
- CONFISCATED relations: +5.0 boost
- SOLD/INHERITED: +3.0 boost
- Document count: ×3.0 multiplier

### Model Selection
- **Haiku** (cheap): complexity ≤ 50
- **Sonnet** (deep): complexity > 50
- Complexity = (entities × 2) + (relations × 1.5) + (documents × 3)

### Session Cost Tracking
- $1 hard limit per session (configurable)
- Blocks generation when exceeded
- Accumulates across all narratives in session

### Caching Strategy
In-memory cache with graph-state invalidation:
- Cache key: `session_id + entity_id + graph_hash`
- Invalidates when any entity or relation data in the constellation changes
- 1-hour TTL
- Easy Redis migration via adapter pattern

## Event Highlighting

Special prominence for:
- **CONFISCATED** - Expropriations (red highlight in UI)
- **SOLD** - Property sales
- **INHERITED** - Estate transfers

```python
for event in result.highlighted_events:
    if event.event_type == "CONFISCATED":
        print(f"🚨 {event.summary}")
        print(f"   Date: {event.date}")
        print(f"   Parties: {', '.join(event.parties_involved)}")
```

## Weight Profile System

Tune centrality scoring for different use cases:

```python
from farmer_factory.narrative import StoryScorer, WEIGHT_PROFILES

# Use built-in profile
scorer = StoryScorer(profile="cuban_restitution")

# Custom weights
custom_weights = {
    "type_weights": {
        EntityType.PROPERTY: 15.0,  # Boost properties more
        EntityType.PERSON: 3.0
    },
    "relation_weights": {
        RelationType.CONFISCATED: 10.0  # Emphasize expropriations
    }
}
scorer = StoryScorer(profile="custom", custom_weights=custom_weights)
```

## Error Handling

```python
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded

try:
    result = generator.generate(
        clicked_node_id="entity_001",
        graph=graph,
        session_id="sess_123",
        max_cost_per_session=1.0
    )
except SessionCostLimitExceeded as e:
    print(f"Session limit exceeded: ${e.current_cost:.2f} > ${e.limit:.2f}")
```

## Testing

```bash
# Unit tests
pytest tests/narrative/ -v

# Integration tests (requires API key)
pytest tests/narrative/test_integration.py -v -m integration

# Specific test
pytest tests/narrative/test_scorer.py::test_confiscation_boosts_score -v
```

## Cost Estimates

Villa Aurelia example (4 entities, 3 relations, 1 doc):
- Complexity: ~26 → Haiku
- Tokens: ~1500 input, ~400 output
- Cost: ~$0.0007 per generation
- With cache: $0 on repeat

Session with 20 narratives:
- Mix of Haiku (80%) and Sonnet (20%)
- Average: ~$0.014 total
- Well under $1 limit

## See Also

- Design: `docs/plans/2026-01-25-narrative-generation-design.md`
- Implementation: `docs/plans/2026-01-25-narrative-generation-implementation-v2.md`
- Schema: `farmer_factory/structure/SCHEMA.md`
