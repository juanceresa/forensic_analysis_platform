# Structure Module

Graph structure module for Civic Table knowledge graph.

## Overview

This module provides the core schema models and graph operations for building and managing the knowledge graph. It uses Pydantic for data validation and NetworkX for graph operations.

## Components

### Schema Models (`schema.py`)

**Verification System:**
- `VerificationTier` - Enum with 4 tiers (TIER_3_AI, TIER_2_ANALYST, TIER_2_INSTITUTIONAL, TIER_1_CERTIFIED)
- `Verification` - Metadata model with tier, confidence, verifier, timestamp, notes

**Entity Types:**
- `EntityType` - Enum for PERSON, PROPERTY, ORGANIZATION, LOCATION, DOCUMENT
- `BaseEntity` - Base model for all entities with verification, timestamps, notes
- `Person` - Person entities (owners, heirs, witnesses, notaries)
- `Property` - Property entities (fincas, haciendas, urban properties)
- `Organization` - Organizations (banks, courts, government agencies)
- `Location` - Locations (cities, provinces, neighborhoods)
- `Document` - Source documents for provenance

**Relations:**
- `RelationType` - Enum with 17 relation types covering ownership, family, boundaries, documents, professional, financial
- `Relation` - Relation model connecting entities with verification and context

**Export Models:**
- `GraphMetadata` - Metadata for graph exports
- `GraphExport` - Complete export format for graph_data.json

### Graph Operations (`graph.py`)

**KnowledgeGraph Class:**
- `__init__(case_id)` - Initialize empty directed graph for a case
- `add_entity(entity)` - Add entity as node with all attributes
- `add_relation(relation)` - Add relation as directed edge (validates source/target exist)
- `get_entity(entity_id)` - Retrieve entity data by ID
- `get_relations(entity_id, direction)` - Get all relations for an entity (in/out/both)
- `get_metadata(factory_version)` - Generate metadata for export

## Usage

### Creating a Knowledge Graph

```python
from farmer_factory.structure import KnowledgeGraph, Person, Verification, VerificationTier, EntityType

# Initialize graph
kg = KnowledgeGraph(case_id="case_001")

# Create an entity
person = Person(
    id="person_123",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",
    verification=Verification(
        tier=VerificationTier.TIER_3_AI,
        confidence=0.92
    ),
    extracted_from="doc_001"
)

# Add to graph
kg.add_entity(person)
```

### Adding Relations

```python
from farmer_factory.structure import Relation, RelationType

# Create relation
relation = Relation(
    id="rel_001",
    type=RelationType.OWNS,
    source_id="person_123",
    target_id="property_456",
    verification=Verification(
        tier=VerificationTier.TIER_3_AI,
        confidence=0.90
    )
)

# Add to graph
kg.add_relation(relation)
```

### Querying the Graph

```python
# Get entity
entity = kg.get_entity("person_123")

# Get all relations for an entity
relations = kg.get_relations("person_123", direction="both")

# Get metadata
metadata = kg.get_metadata(factory_version="1.0.0")
```

## Verification Tiers

All entities and relations must have verification metadata:

| Tier | Label | Provider | Display |
|------|-------|----------|---------|
| TIER_3_AI | AI Extracted | Civic Table platform | Grey + disclaimer |
| TIER_2_ANALYST | Analyst Verified | Civic Table analyst | Gold badge |
| TIER_2_INSTITUTIONAL | Farmer House Verified | Farmer House (optional) | Gold + FH badge |
| TIER_1_CERTIFIED | Legally Certified | External legal body | Blue certification |

## Testing

Run tests for this module:

```bash
python -m pytest tests/structure/ -v
```

## Design Principles

- **Type Safety**: All models use Pydantic for validation
- **Verification**: Every entity and relation requires verification metadata
- **Immutability**: Entities are immutable once created (verification can be upgraded)
- **Graph Integrity**: Relations require both source and target entities to exist
- **Historical Data**: Flexible string dates for historical documents (1916-1961 era)
