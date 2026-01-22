# Structure Module Integration Design - Graph Building from Extracted Entities

> **Created:** 2026-01-22
> **Status:** Approved for Implementation
> **Scope:** MVP1 - Graph building with entity resolution and JSON export

---

## Overview

The structure module integrates with the extract module to build a unified knowledge graph from multi-document extractions. It handles entity deduplication, conflict resolution, and exports JSON for the frontend visualization.

**Pipeline Flow:**
```
ExtractionResult (from extract module)
    ↓
GraphBuilder.add_extraction()
    ↓
EntityResolver.resolve_entity()
    ↓
KnowledgeGraph.add_entity() / add_relation()
    ↓
GraphExporter.to_json()
    ↓
graph_data.json (for frontend)
```

---

## Architecture

### Three Main Components

**1. Graph Builder (`builder.py`)**
- Takes ExtractionResult objects and builds the graph
- Routes entities to resolver for deduplication
- Adds merged entities and relations to KnowledgeGraph
- Tracks processing statistics

**2. Entity Resolver (`resolver.py`)**
- Handles deduplication using fuzzy string matching
- Compares entity attributes (dates, locations, roles)
- Merges similar entities with similarity score > 0.85
- Preserves conflicting values as lists with document provenance

**3. Graph Exporter (`exporter.py`)**
- Converts NetworkX graph to force-graph JSON format
- Serializes Pydantic models to JSON-compatible dicts
- Includes metadata (case_id, counts, verification stats)
- Validates output schema before writing

---

## Component Details

### GraphBuilder (`builder.py`)

```python
class GraphBuilder:
    """Orchestrates graph construction from extraction results."""

    def __init__(self, knowledge_graph: KnowledgeGraph, resolver: EntityResolver):
        """
        Initialize graph builder.

        Args:
            knowledge_graph: KnowledgeGraph instance to build into
            resolver: EntityResolver for deduplication
        """
        self.graph = knowledge_graph
        self.resolver = resolver
        self.processing_stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "entities_merged": 0,
            "relations_added": 0
        }

    def add_extraction(self, extraction: ExtractionResult) -> None:
        """
        Add entities and relations from extraction result.

        Process:
        1. Resolve and add entities (with deduplication)
        2. Add relations (after entities exist)
        3. Update processing stats

        Args:
            extraction: ExtractionResult from extract module
        """

    def build_from_document_batch(
        self,
        extractions: List[ExtractionResult]
    ) -> None:
        """
        Process multiple document extractions.

        Args:
            extractions: List of ExtractionResult objects
        """
```

**Process Flow:**
1. For each entity in `extraction.entities`:
   - Check if similar entity exists (via resolver)
   - If yes: merge attributes, track source documents
   - If no: add as new entity
2. For each relation in `extraction.relations`:
   - Validate source/target entities exist in graph
   - Add relation with verification metadata
3. Update processing statistics

**Statistics Tracking:**
- `documents_processed`: Count of ExtractionResult objects processed
- `entities_extracted`: Total entities from all extractions
- `entities_merged`: Count of successful merges
- `relations_added`: Total relations added to graph

---

### EntityResolver (`resolver.py`)

```python
class EntityResolver:
    """Handles entity deduplication using fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize entity resolver.

        Args:
            similarity_threshold: Minimum similarity score for merge (0.0-1.0)
        """
        self.threshold = similarity_threshold
        self.entity_index = {}  # {entity_type: [entity_ids]}

    def find_similar_entity(
        self,
        entity: BaseEntity,
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Find existing entity that matches this one.

        Uses fuzzy string matching on name and attribute comparison.

        Args:
            entity: New entity to match
            graph: KnowledgeGraph to search

        Returns:
            Entity ID if match found, None otherwise
        """

    def merge_entities(
        self,
        existing: Dict[str, Any],
        new: BaseEntity
    ) -> Dict[str, Any]:
        """
        Merge new entity data into existing entity.

        For conflicting fields, creates lists with document provenance:
        Example: birth_date = ["1920 (doc_001)", "1922 (doc_005)"]

        Args:
            existing: Existing entity data from graph
            new: New entity to merge in

        Returns:
            Merged entity data dictionary
        """
```

**Matching Logic by Entity Type:**

- **Person**:
  - Name fuzzy match ≥ 85%
  - Birth date comparison (if available)
  - Nationality match (if available)

- **Property**:
  - Address fuzzy match ≥ 80%
  - Registry number exact match (if available)

- **Organization**:
  - Name fuzzy match ≥ 90%
  - Location comparison

- **Location**:
  - Name exact match
  - Location type match

- **Document**:
  - Registry number exact match OR
  - Date + document type match

**Conflict Resolution:**
- **String fields**: Store as list if different values
- **Dates**: Store all variants with source documents
- **Lists**: Union of all values from all sources
- **Single values**: Prefer value from higher confidence extraction

**Provenance Format:**
```python
# Single value from one source
birth_date = "1920"
extracted_from = "doc_001"

# Conflicting values from multiple sources
birth_date = ["1920 (doc_001)", "1922 (doc_005)"]
extracted_from = ["doc_001", "doc_005"]
```

---

### GraphExporter (`exporter.py`)

```python
class GraphExporter:
    """Converts NetworkX graph to force-graph JSON format."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize graph exporter.

        Args:
            knowledge_graph: KnowledgeGraph to export
        """
        self.graph = knowledge_graph

    def to_json(self, factory_version: str) -> Dict[str, Any]:
        """
        Export graph to force-graph JSON format.

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            Complete JSON structure with nodes, links, metadata
        """

    def save(self, output_path: Path, factory_version: str) -> None:
        """
        Save graph_data.json to file.

        Args:
            output_path: Path to write JSON file
            factory_version: Version string for metadata
        """
```

**Output Format:**
```json
{
  "nodes": [
    {
      "id": "person_123",
      "type": "PERSON",
      "name": "Juan Pérez García",
      "alternate_names": ["Don Juan Pérez"],
      "birth_date": ["1920 (doc_001)", "1922 (doc_005)"],
      "nationality": "Cuban",
      "roles": ["owner", "seller"],
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.88,
        "verified_by": null,
        "verified_at": null,
        "notes": null
      },
      "extracted_from": ["doc_001", "doc_005"],
      "created_at": "2026-01-22T15:30:00",
      "updated_at": "2026-01-22T15:35:00"
    }
  ],
  "links": [
    {
      "source": "person_123",
      "target": "property_456",
      "type": "OWNS",
      "relation_id": "rel_001",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.90
      },
      "date": "1958-03-15",
      "document_id": "doc_001"
    }
  ],
  "metadata": {
    "case_id": "case_001",
    "entity_count": 42,
    "relation_count": 67,
    "document_count": 5,
    "created_at": "2026-01-22T15:30:00",
    "updated_at": "2026-01-22T15:35:00",
    "factory_version": "1.0.0",
    "processing_stats": {
      "documents_processed": 5,
      "entities_extracted": 67,
      "entities_merged": 25,
      "relations_added": 67
    }
  }
}
```

**Key Features:**
- **Merged entities**: Multiple source documents in `extracted_from` array
- **Conflicting values**: Stored as arrays with provenance strings
- **Verification metadata**: All verification info preserved
- **Force-graph compatibility**: Standard `{nodes, links}` structure for react-force-graph-2d

---

## Error Handling

### GraphBuilder Errors

**Invalid extraction:**
- Log warning with details
- Skip malformed entities
- Continue processing remaining entities

**Relation validation failure:**
- Skip relation if source/target missing
- Log error with entity IDs
- Don't fail entire extraction

**Merge conflicts:**
- Default to keeping all conflicting values
- Never fail on conflict
- Log info about merged entity

### EntityResolver Errors

**Fuzzy matching timeout:**
- Fall back to exact string matching
- Log warning about degraded matching
- Continue processing

**Invalid similarity score:**
- Default to no match (create new entity)
- Log error about calculation failure
- Ensure graph integrity

**Circular merge detection:**
- Prevent A→B→A merge loops
- Log warning about potential duplicate
- Create separate entity

### GraphExporter Errors

**Serialization failure:**
- Validate Pydantic models before export
- Report specific field causing error
- Raise exception with clear message

**File write error:**
- Don't corrupt existing file
- Atomic write (temp file + rename)
- Raise exception with path details

**Invalid JSON:**
- Validate output structure before writing
- Provide detailed error with location
- Include sample of problematic data

### Recovery Strategy

**Partial Success:**
- Process all valid entities/relations
- Log all errors encountered
- Return success with error summary

**Never Fail Pipeline:**
- One bad entity doesn't stop processing
- Collect errors and report at end
- Maintain graph integrity throughout

---

## Testing Strategy

### Unit Tests

**`test_builder.py`:**
- GraphBuilder initialization
- Single extraction processing
- Batch extraction processing
- Statistics tracking accuracy
- Error handling for invalid extractions

**`test_resolver.py`:**
- Fuzzy matching at various thresholds
- Entity type-specific matching logic
- Conflict resolution with multiple sources
- Provenance string formatting
- Similarity calculation edge cases

**`test_exporter.py`:**
- JSON structure generation
- Pydantic model serialization
- Metadata completeness
- File I/O operations
- Schema validation

**`test_integration.py`:**
- Full pipeline: extract → structure → JSON
- Multi-document graph building
- Entity deduplication across documents
- Export format compatibility
- End-to-end error handling

### Test Coverage

**Entity Resolution:**
- High similarity (>0.95) - should merge
- Threshold similarity (0.85) - should merge
- Low similarity (<0.85) - should not merge
- Identical entities - should merge perfectly
- Conflicting attributes - should preserve all

**Graph Integrity:**
- Relations require valid source/target entities
- No orphaned relations
- Circular relation handling
- Multiple relations between same entities

**Export Validation:**
- All nodes have required fields
- All links reference valid node IDs
- Metadata counts match graph
- JSON is valid and parseable

**Edge Cases:**
- Empty graph export
- Single entity graph
- Graph with no relations
- Large graph (1000+ entities)
- Deep conflict chains (5+ sources)

### Mocked Dependencies

**Extract Module:**
- Use sample ExtractionResult objects
- Pre-defined entities with known conflicts
- Test data covers all entity types

**File I/O:**
- Mock file writes in unit tests
- Use temp directories for integration tests
- Fast execution, predictable behavior

---

## Data Flow Example

**Input (from extract module):**
```python
# Document 1 extraction
extraction_1 = ExtractionResult(
    entities=[
        Person(id="p1", name="Juan Pérez", birth_date="1920", ...),
        Property(id="prop1", address="Miramar 234", ...)
    ],
    relations=[
        Relation(source_id="p1", target_id="prop1", type=OWNS, ...)
    ],
    ...
)

# Document 2 extraction (same person, conflicting birth date)
extraction_2 = ExtractionResult(
    entities=[
        Person(id="p2", name="Juan Pérez García", birth_date="1922", ...),
    ],
    ...
)
```

**Processing:**
1. GraphBuilder receives extraction_1
   - Resolver: No similar entities found
   - Adds Person p1, Property prop1
   - Adds OWNS relation
2. GraphBuilder receives extraction_2
   - Resolver: Finds p1 similar to p2 (name match 95%)
   - Merges: birth_date becomes ["1920 (doc_001)", "1922 (doc_002)"]
   - Updates extracted_from to ["doc_001", "doc_002"]

**Output (graph_data.json):**
```json
{
  "nodes": [
    {
      "id": "p1",
      "name": "Juan Pérez García",
      "birth_date": ["1920 (doc_001)", "1922 (doc_002)"],
      "extracted_from": ["doc_001", "doc_002"],
      "verification": {"tier": "TIER_3_AI", "confidence": 0.88}
    }
  ],
  "links": [...],
  "metadata": {...}
}
```

---

## Dependencies

**New Dependencies:**
- `rapidfuzz` or `fuzzywuzzy` - Fuzzy string matching for entity resolution

**Existing Dependencies:**
- `networkx` - Already used in KnowledgeGraph
- `pydantic` - Already used for schema models
- Extract module - ExtractionResult, entities, relations

---

## See Also

- `docs/plans/2026-01-22-extract-module-design.md`: Extract module specification
- `farmer_factory/structure/README.md`: Existing structure module docs
- `farmer_factory/structure/schema.py`: Entity and relation schemas
- `farmer_factory/structure/graph.py`: Existing KnowledgeGraph class
- `.claude/CLAUDE.md`: Project constraints and verification tiers
