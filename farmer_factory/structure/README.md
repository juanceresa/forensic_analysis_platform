# Structure Module

> **Version:** 1.2.0
> **Last Updated:** 2026-01-25
> **Status:** Active with ML-based entity resolution

Graph construction and entity deduplication for Civic Table knowledge graph.

---

## Overview

This module transforms extracted entities into a unified knowledge graph with ML-based deduplication. It uses:

- **Pydantic** - Schema validation and type safety
- **NetworkX** - Graph data structure and operations
- **dedupe** - Machine learning entity resolution
- **Structured extraction** - Full biographical and family relationship data (v1.2.0)

---

## Components

### Complete Schema Specification

See `SCHEMA.md` in this directory for:
- Full JSON schema definitions
- TypeScript type definitions
- Force-graph export format
- Validation rules

`SCHEMA.md` is the canonical schema reference for both Python (Pydantic) and TypeScript implementations.

### Data Dictionary

See `DATA_DICTIONARY.md` for field-level reference:
- All entity and relation fields
- Field types and constraints
- Examples and usage notes

### 1. Schema Models (`schema.py`)

#### Verification System
- `VerificationTier` - 4-tier system (TIER_3_AI → TIER_1_CERTIFIED)
- `Verification` - Metadata: tier, confidence, verifier, timestamp, notes

#### Entity Types

**Person** (with family relationships - v1.2.0):
```python
class Person(BaseEntity):
    # Core identity
    name: str
    alternate_names: List[str]

    # Demographics
    birth_date: Optional[str]
    death_date: Optional[str]
    nationality: Optional[str]
    residence: Optional[str]
    profession: Optional[str]
    marital_status: Optional[str]

    # Family relationships (NEW in v1.2.0)
    mother: Optional[str]  # Name as string
    father: Optional[str]
    spouse: Optional[str]
    children: List[str]
    siblings: List[str]

    # Roles
    roles: List[str]
```

**Property:**
```python
class Property(BaseEntity):
    name: Optional[str]
    property_type: Optional[str]
    location_id: Optional[str]
    address: Optional[str]
    description: Optional[str]
    area: Optional[float]
    area_unit: Optional[str]
    registry_number: Optional[str]
    cadastral_info: Optional[str]
    folio_number: Optional[str]
```

**Organization, Location, Document** - See `schema.py` for full definitions

#### Relations
- `RelationType` - Enum with 20+ types:
  - Ownership: OWNS, SOLD, BOUGHT, INHERITED, CONFISCATED
  - Family: SPOUSE_OF, CHILD_OF, HEIR_OF, RELATED_TO
  - Document: MENTIONED_IN, WITNESSED, NOTARIZED
  - Geographic: LOCATED_IN, REGISTERED_IN
  - Financial: CREDITOR_OF, DEBTOR_OF

- `Relation` - Connects entities with verification and context

#### Export Models
- `GraphMetadata` - Statistics and processing info
- `GraphExport` - Force-graph format for visualization
  - Export uses top-level `nodes` + `links`, with `metadata` carrying
    `verification_distribution`, `entity_type_summary`, and `date_range`

---

### 2. Knowledge Graph (`graph.py`)

Core graph data structure using NetworkX:

```python
kg = KnowledgeGraph(case_id="CASE-CERESA")

# Add entities
kg.add_entity(person)
kg.add_entity(property)

# Add relations
kg.add_relation(owns_relation)

# Query
entity = kg.get_entity("person_123")
relations = kg.get_relations("person_123", direction="out")
```

**Notes:**
- Graph uses a multi-edge directed model, so multiple relations between the same
  node pair are preserved (e.g., OWNS + SOLD).

**Methods:**
- `add_entity(entity)` - Add node with all attributes
- `add_relation(relation)` - Add directed edge (validates endpoints exist)
- `get_entity(entity_id)` - Retrieve entity data
- `get_relations(entity_id, direction)` - Get relations (in/out/both)
- `get_metadata(factory_version)` - Generate export metadata

---

### 3. Entity Resolution (`resolver.py`)

**ML-based deduplication** using the dedupe library.

#### DedupeEntityResolver

```python
resolver = DedupeEntityResolver(threshold=0.5)

# Finds duplicates automatically
match_id = resolver.find_similar_entity(new_person, graph)

if match_id:
    # Merge with existing entity
    merged = resolver.merge_entities(existing, new_person, confidence=0.92)
else:
    # Add as new entity
    graph.add_entity(new_person)
```

**Key Features:**
- Multi-attribute matching (name + birth_date + residence + profession)
- Confidence-weighted merging (high confidence picks better value)
- Separate trained models per entity type (PERSON, PROPERTY, etc.)
- Preserves source provenance (`extracted_from` tracks all documents)

**Matching Strategy:**

| Confidence | Action |
|------------|--------|
| ≥ 0.8 | Auto-merge, choose better value for conflicts |
| 0.5-0.79 | Merge with conflict lists (both values preserved) |
| < 0.5 | Keep as separate entities |

#### Training Models

Interactive training session:

```bash
python cli.py train-deduplication CASE-ID --entity-type PERSON
```

Trains using active learning:
- Shows pairs of entities
- User labels: y (same), n (different), u (unsure)
- Collects ~30 examples per type
- Saves model to `structure/models/{type}_settings`

**Current Status:**
- ✅ PERSON model implemented and trained
- ⏳ LOCATION, PROPERTY, ORGANIZATION - trainable but not yet trained

---

### 4. Dedupe Configuration (`dedupe_config.py`)

Defines which fields to use for matching each entity type:

**PERSON_FIELDS:**
- ✅ name, birth_date, death_date, residence, profession, nationality, marital_status
- ❌ Family fields excluded (mother, father, spouse, children, siblings)

**Why exclude family fields?**
- Siblings share parents → matching on "father" would merge siblings into one person
- Family data is for genealogical research, not deduplication
- Still stored on entities and used for graph edges

**PROPERTY_FIELDS:**
- name, property_type, location_id, area

**LOCATION_FIELDS:**
- name, location_type, country, parent_location_id

**ORGANIZATION_FIELDS:**
- name, org_type, location_id

---

### 5. Graph Builder (`builder.py`)

Orchestrates graph construction with automatic deduplication:

```python
from farmer_factory.structure import (
    KnowledgeGraph,
    DedupeEntityResolver,
    GraphBuilder
)

# Initialize
graph = KnowledgeGraph(case_id="CASE-CERESA")
resolver = DedupeEntityResolver(threshold=0.5)
builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

# Process extractions (deduplication happens automatically)
for extraction in extractions:
    builder.add_extraction(extraction)

# Get statistics
stats = builder.processing_stats
# {
#   'documents_processed': 18,
#   'entities_extracted': 207,
#   'entities_merged': 150,  # Duplicates merged!
#   'relations_added': 40
# }
```

**What it does:**
1. Creates a DOCUMENT entity for each extraction (auto-generated)
2. Receives entities from extraction pipeline
3. For each entity, checks for duplicates using trained dedupe model
4. If match found → merge with existing entity
5. If no match → add as new entity
6. Adds relations with entity ID matching
7. Tracks statistics

> **Note:** Entity counts in `processing_stats["entities_extracted"]` include auto-created DOCUMENT entities.

**Benefits:**
- Automatic deduplication during processing
- No manual review required for obvious duplicates
- Preserves provenance (all source documents tracked)

---

### 6. Graph Exporter (`exporter.py`)

Exports to force-graph JSON format for visualization:

```python
from farmer_factory.structure import GraphExporter

exporter = GraphExporter(knowledge_graph=graph)
exporter.save(
    output_path="output/graph_data.json",
    factory_version="1.2.0"
)
```

**Output format:**
```json
{
  "metadata": {
    "case_id": "CASE-CERESA",
    "entity_count": 57,
    "relation_count": 40,
    "factory_version": "1.2.0"
  },
  "nodes": [
    {
      "id": "person_abc123",
      "entity_type": "PERSON",
      "name": "Mario Ceresa",
      "mother": "María López de Queral",
      "father": "Juan Ceresa",
      "verification": { ... },
      "extracted_from": ["doc_1", "doc_2", "doc_3"]
    }
  ],
  "links": [
    {
      "source": "person_abc123",
      "target": "property_xyz789",
      "relation_type": "OWNS",
      "verification": { ... }
    }
  ]
}
```

---

## Complete Usage Example

```python
from pathlib import Path
from farmer_factory.structure import (
    KnowledgeGraph,
    DedupeEntityResolver,
    GraphBuilder,
    GraphExporter,
    Person,
    Property,
    Relation,
    Verification,
    VerificationTier,
    EntityType,
    RelationType
)

# 1. Initialize components
graph = KnowledgeGraph(case_id="CASE-CERESA")
resolver = DedupeEntityResolver(threshold=0.5)  # Loads trained models
builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

# 2. Create entities (normally from extraction pipeline)
person1 = Person(
    id="temp_001",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",
    mother="María López de Queral",  # Family relationships
    father="Juan Ceresa",
    birth_date="1920",
    residence="Camagüey",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.92),
    extracted_from="doc_001"
)

# 3. Add through builder via extraction (automatic deduplication)
# Note: Use add_extraction() with ExtractionResult, not add_entity() directly
from farmer_factory.extract import ExtractionResult
from farmer_factory.prepare import DocumentPath

extraction = ExtractionResult(
    entities=[person1],
    relations=[],
    ocr_result=None,
    confidence_scores={"overall": 0.92},
    path=DocumentPath.TYPED,
    processing_metadata={}
)
builder.add_extraction(extraction)

# Later, same person from different document
person2 = Person(
    id="temp_002",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",  # Same person
    profession="industrialist",
    residence="Camagüey",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.88),
    extracted_from="doc_005"
)

extraction2 = ExtractionResult(
    entities=[person2],
    relations=[],
    ocr_result=None,
    confidence_scores={"overall": 0.88},
    path=DocumentPath.TYPED,
    processing_metadata={}
)
builder.add_extraction(extraction2)
# → Dedupe detects match → Merges into person1
# → person1 now has: mother, father, profession, extracted_from=["doc_001", "doc_005"]

# 4. Add relations
relation = Relation(
    id="rel_001",
    type=RelationType.OWNS,
    source_id="person_abc123",  # Final merged ID
    target_id="property_xyz789",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.90)
)
builder.add_relation(relation)

# 5. Export
exporter = GraphExporter(knowledge_graph=graph)
exporter.save(Path("output/graph_data.json"), factory_version="1.2.0")

# 6. Check statistics
stats = builder.processing_stats
print(f"Entities extracted: {stats['entities_extracted']}")
print(f"Entities merged: {stats['entities_merged']}")
print(f"Final unique entities: {stats['entities_extracted'] - stats['entities_merged']}")
```

---

## Entity Deduplication Deep Dive

### How Matching Works

When a new entity arrives:

1. **Check for trained model**
   - If no model for this type → skip deduplication, add as new
   - If model exists → proceed to matching

2. **Prepare candidate entities**
   - Get all existing entities of same type from graph
   - Convert to dedupe format (dict with matching fields)

3. **Run ML model**
   - dedupe compares new entity to each candidate
   - Returns probabilities for each pair
   - Threshold (default 0.5) determines if it's a match

4. **Merge or add**
   - If match found → merge entities, preserve provenance
   - If no match → add as new entity

### Merge Logic

**High confidence (≥0.8):**
- Choose better value based on confidence scores
- Example: `birth_date="1920"` (conf 0.9) overwrites `birth_date="1922"` (conf 0.7)

**Medium confidence (0.5-0.79):**
- Create conflict lists with provenance
- Example: `birth_date=["1920 (doc_1)", "1922 (doc_5)"]`
- Analyst reviews later

**Always:**
- Combine `extracted_from` lists
- Preserve order (first document first)
- Keep highest confidence verification

---

## Testing

```bash
# Unit tests
python -m pytest tests/structure/test_resolver.py -v
python -m pytest tests/structure/test_builder.py -v
python -m pytest tests/structure/test_graph.py -v

# Integration test
python cli.py process TEST-CERESA --force-typed
python cli.py train-deduplication TEST-CERESA --entity-type PERSON
```

---

## Verification Tiers

All entities and relations require verification metadata:

| Tier | Label | Provider | Color | Use Case |
|------|-------|----------|-------|----------|
| TIER_3_AI | AI Extracted | Claude API | Grey | Automated extraction |
| TIER_2_ANALYST | Analyst Verified | Civic Table analyst | Gold | Human review |
| TIER_2_INSTITUTIONAL | Farmer House Verified | Farmer House (optional) | Gold+FH | Institutional partnership |
| TIER_1_CERTIFIED | Legally Certified | External legal body | Blue | Court/legal validation |

**MVP1 Scope:**
- All data starts as TIER_3_AI (automated)
- Analyst UI promotes to TIER_2_ANALYST
- TIER_2_INSTITUTIONAL designed but not active yet
- TIER_1_CERTIFIED is external legal process

---

## Design Principles

- **Type Safety** - All models use Pydantic validation
- **ML-based Deduplication** - Active learning for high accuracy
- **Provenance Tracking** - Every entity tracks source documents
- **Verification Required** - No unverified data in graph
- **Graph Integrity** - Relations require both endpoints to exist
- **Family Relationships** - Stored on entities AND as graph edges
- **Historical Flexibility** - String dates for 1916-1961 era documents

---

## Version History

**v1.2.0 (2026-01-25):**
- Added family relationship fields to Person schema
- Updated dedupe config with marital_status
- Documented why family fields excluded from matching
- Updated all examples and documentation

**v1.1.0 (2026-01-24):**
- Replaced fuzzy matching with ML-based dedupe
- Added DedupeEntityResolver
- Added interactive training workflow
- Added GraphBuilder orchestration

**v1.0.0 (2026-01-22):**
- Initial schema implementation
- Basic graph operations
- Fuzzy matching (deprecated)

---

*For implementation details, see source files in `farmer_factory/structure/`*
