# Export Module

JSON export logic for Civic Table knowledge graph.

## Overview

This module handles exporting knowledge graphs to JSON format for consumption by the Vault (Next.js frontend). It generates `graph_data.json` files with complete graph data, metadata, and summaries.

## Components

### GraphExporter (`exporter.py`)

**Purpose**: Export knowledge graphs to JSON format with validation and summaries.

**Methods:**
- `__init__(graph)` - Initialize exporter with a KnowledgeGraph
- `export_to_dict(factory_version)` - Export graph to dictionary format
- `export_to_json(output_path, factory_version)` - Write graph to JSON file
- `_calculate_verification_summary()` - Calculate counts by verification tier
- `_calculate_entity_type_summary()` - Calculate counts by entity type

## JSON Output Format

The exported `graph_data.json` follows this structure:

```json
{
  "metadata": {
    "case_id": "case_001",
    "created_at": "2026-01-22T10:30:00",
    "updated_at": "2026-01-22T10:30:00",
    "factory_version": "1.0.0",
    "entity_count": 150,
    "relation_count": 220,
    "document_count": 12,
    "processing_stats": {},
    "verification_distribution": {
      "TIER_3_AI": 280,
      "TIER_2_ANALYST": 45,
      "TIER_2_INSTITUTIONAL": 10,
      "TIER_1_CERTIFIED": 5
    },
    "entity_type_summary": {
      "PERSON": 50,
      "PROPERTY": 40,
      "ORGANIZATION": 20,
      "LOCATION": 30,
      "DOCUMENT": 10
    },
    "date_range": null
  },
  "nodes": [
    {
      "id": "person_123",
      "entity_type": "PERSON",
      "name": "Mario Ceresa",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.92
      },
      "extracted_from": "doc_001",
      ...
    }
  ],
  "links": [
    {
      "source": "person_123",
      "target": "property_456",
      "relation_id": "rel_001",
      "relation_type": "OWNS",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.90
      },
      ...
    }
  ]
}
```

**Note:** The export format uses `links` (not `edges`) and includes `verification_distribution` and `entity_type_summary` under `metadata`.

## Usage

### Basic Export

```python
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.export import GraphExporter

# Create and populate graph
kg = KnowledgeGraph(case_id="case_001")
# ... add entities and relations ...

# Export to JSON
exporter = GraphExporter(kg)
exporter.export_to_json(
    output_path=Path("output/graph_data.json"),
    factory_version="1.0.0"
)
```

### Export to Dictionary

```python
# Get dictionary format (useful for API responses)
data = exporter.export_to_dict(factory_version="1.0.0")

# Access components
metadata = data["metadata"]
nodes = data["nodes"]
links = data["links"]
verification_distribution = metadata["verification_distribution"]
entity_type_summary = metadata["entity_type_summary"]
```

## Summaries

The exporter includes two summaries in the metadata:

### Verification Summary

Counts all entities and relations by verification tier:

```python
{
    "TIER_3_AI": 280,        # AI extracted
    "TIER_2_ANALYST": 45,    # Analyst verified
    "TIER_2_INSTITUTIONAL": 10,  # Farmer House verified
    "TIER_1_CERTIFIED": 5    # Legally certified
}
```

### Entity Type Summary

Counts all entities by type:

```python
{
    "PERSON": 50,
    "PROPERTY": 40,
    "ORGANIZATION": 20,
    "LOCATION": 30,
    "DOCUMENT": 10
}
```

## File Output

The exporter:
- Creates parent directories if they don't exist
- Writes UTF-8 encoded JSON
- Uses 2-space indentation for readability
- Includes `ensure_ascii=False` for proper international character handling
- Uses `default=str` to handle datetime serialization

## Testing

Run tests for this module:

```bash
python -m pytest tests/export/ -v
```

## Future Enhancements

- **Supabase Upload**: Upload JSON to Supabase Storage for frontend consumption
- **Date Range Calculation**: Extract min/max dates from document entities
- **Schema Validation**: Validate against GraphExport Pydantic model before writing
- **Compression**: Optional gzip compression for large graphs
- **Incremental Export**: Export only changed nodes/edges since last export
