# Farmer House Forensic Intelligence Platform — JSON Schema Specification

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.3.0
> **Last Updated:** 2026-01-27
> **Status:** MVP1 Schema (current `graph_data.json` export)

---

## Overview

This document defines the JSON contract for `graph_data.json`, the primary output of Zone A (The Factory) consumed by Zone B (The Vault). It matches the live Pydantic models in `farmer_factory/structure/schema.py` and the exporter output in `farmer_factory/structure/exporter.py`.

Key decisions:
- Nodes are **flattened** (entity fields live on the node itself; no nested `data` object).
- Node types use `entity_type`; node display name is `name`.
- Link types use `relation_type`.
- Provenance uses `extracted_from` as a **comma-delimited string** of document IDs.
- Metadata lives under `metadata` and includes verification distribution and entity type summaries.
- **Entity and relation types are domain-configurable** (loaded from YAML configuration).

---

## Domain Configuration

Entity types and relation types are **dynamically loaded** from domain configuration rather than hardcoded. The default domain is `cuban_property`.

### How Types Are Determined

```python
from farmer_factory.domains import domain_registry
from farmer_factory.structure.schema import get_valid_entity_types, get_valid_relation_types

# Without active domain - uses defaults
entity_types = get_valid_entity_types()
# {"PERSON", "PROPERTY", "ORGANIZATION", "LOCATION", "DOCUMENT"}

# With active domain - uses domain config
domain_registry.set_active("cuban_property")
entity_types = get_valid_entity_types()
# Types from farmer_factory/domains/configs/cuban_property/domain.yaml
```

### Refreshing Types After Domain Change

After changing the active domain, call `refresh_type_enums()` to update dynamic enums:

```python
from farmer_factory.structure.schema import refresh_type_enums
refresh_type_enums()
```

See `farmer_factory/domains/README.md` for full domain configuration documentation.

---

## Root Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["metadata", "nodes", "links"],
  "properties": {
    "metadata": { "$ref": "#/$defs/GraphMetadata" },
    "nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/Node" }
    },
    "links": {
      "type": "array",
      "items": { "$ref": "#/$defs/Link" }
    }
  }
}
```

---

## Metadata

```json
{
  "$defs": {
    "GraphMetadata": {
      "type": "object",
      "required": [
        "case_id",
        "created_at",
        "updated_at",
        "factory_version",
        "entity_count",
        "relation_count",
        "document_count"
      ],
      "properties": {
        "case_id": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" },
        "factory_version": { "type": "string" },
        "entity_count": { "type": "integer", "minimum": 0 },
        "relation_count": { "type": "integer", "minimum": 0 },
        "document_count": { "type": "integer", "minimum": 0 },
        "processing_stats": { "type": "object" },
        "verification_distribution": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "entity_type_summary": {
          "type": "object",
          "additionalProperties": { "type": "integer" }
        },
        "date_range": {
          "type": "object",
          "properties": {
            "earliest_document": { "type": ["string", "null"] },
            "latest_document": { "type": ["string", "null"] },
            "earliest_event": { "type": ["string", "null"] },
            "latest_event": { "type": ["string", "null"] }
          }
        },
        "domain": {
          "type": ["string", "null"],
          "description": "Domain configuration used for processing (e.g., 'cuban_property')"
        }
      }
    }
  }
}
```

---

## Verification

```json
{
  "$defs": {
    "Verification": {
      "type": "object",
      "required": ["tier", "confidence"],
      "properties": {
        "tier": {
          "type": "string",
          "enum": [
            "TIER_3_AI",
            "TIER_2_ANALYST",
            "TIER_2_INSTITUTIONAL",
            "TIER_1_CERTIFIED"
          ]
        },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
        "verified_by": { "type": ["string", "null"] },
        "verified_at": { "type": ["string", "null"], "format": "date-time" },
        "notes": { "type": ["string", "null"] }
      }
    }
  }
}
```

---

## Node Schema

```json
{
  "$defs": {
    "Node": {
      "type": "object",
      "required": ["id", "entity_type", "verification", "extracted_from"],
      "properties": {
        "id": { "type": "string" },
        "entity_type": {
          "type": "string",
          "enum": ["PERSON", "PROPERTY", "ORGANIZATION", "LOCATION", "DOCUMENT"]
        },
        "verification": { "$ref": "#/$defs/Verification" },
        "extracted_from": {
          "type": "string",
          "description": "Comma-delimited document IDs; split + trim on the frontend"
        },
        "created_at": { "type": "string", "format": "date-time" },
        "updated_at": { "type": "string", "format": "date-time" },
        "notes": { "type": ["string", "null"] }
      }
    }
  }
}
```

### Entity-Specific Fields

#### PERSON
- `name` (string, required)
- `alternate_names` (string[])
- `birth_date`, `death_date`, `nationality`, `residence`, `profession`, `marital_status`
- `mother`, `father`, `spouse` (string)
- `children`, `siblings` (string[])
- `roles` (string[])

#### PROPERTY
- `name` (string, optional)
- `property_type`, `location_id`, `address`, `description`
- `area` (number), `area_unit` (string)
- `registry_number`, `cadastral_info`, `folio_number`

#### ORGANIZATION
- `name` (string, required)
- `org_type`, `location_id`, `address`

#### LOCATION
- `name` (string, required)
- `location_type`, `parent_location_id`, `country`

#### DOCUMENT
- `title` (string, optional)
- `document_type` (string, required)
- `document_number`, `date`, `issuer`, `location_id`
- `file_path` (string, required)
- `page_count` (integer, required)
- `ocr_text` (string, optional)
- `language` (string, default "es")

---

## Link Schema

```json
{
  "$defs": {
    "Link": {
      "type": "object",
      "required": ["source", "target", "relation_type", "verification"],
      "properties": {
        "relation_id": { "type": "string" },
        "source": { "type": "string" },
        "target": { "type": "string" },
        "relation_type": {
          "type": "string",
          "enum": [
            "OWNS",
            "OWNED",
            "INHERITED",
            "SOLD",
            "SOLD_TO",
            "BOUGHT",
            "PURCHASED_FROM",
            "CONFISCATED",
            "SPOUSE_OF",
            "CHILD_OF",
            "HEIR_OF",
            "RELATED_TO",
            "BORDERS_NORTH",
            "BORDERS_SOUTH",
            "BORDERS_EAST",
            "BORDERS_WEST",
            "MENTIONED_IN",
            "WITNESSED",
            "WITNESSED_BY",
            "NOTARIZED",
            "NOTARIZED_BY",
            "ISSUED_BY",
            "REPRESENTED_BY",
            "EMPLOYED_BY",
            "LOCATED_IN",
            "REGISTERED_IN",
            "CREDITOR_OF",
            "DEBTOR_OF"
          ]
        },
        "verification": { "$ref": "#/$defs/Verification" },
        "date": { "type": ["string", "null"] },
        "amount": { "type": ["number", "null"] },
        "currency": { "type": ["string", "null"] },
        "property_id": { "type": ["string", "null"] },
        "document_id": { "type": ["string", "null"] },
        "evidence": { "type": ["string", "null"] },
        "notes": { "type": ["string", "null"] }
      }
    }
  }
}
```

---

## Derived Fields (Exporter)

The exporter adds convenience fields for sorting:
- Nodes: `birth_date_sortable`, `death_date_sortable`, `date_sortable`
- Links: `date_sortable`
- Metadata: `date_range` (earliest/latest)

These fields are **computed** and not required for ingestion.

---

## TypeScript Types (Frontend)

```typescript
export type VerificationTier =
  | 'TIER_3_AI'
  | 'TIER_2_ANALYST'
  | 'TIER_2_INSTITUTIONAL'
  | 'TIER_1_CERTIFIED';

export interface Verification {
  tier: VerificationTier;
  confidence: number;
  verified_by?: string | null;
  verified_at?: string | null;
  notes?: string | null;
}

export type EntityType =
  | 'PERSON'
  | 'PROPERTY'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'DOCUMENT';

export interface NodeBase {
  id: string;
  entity_type: EntityType;
  verification: Verification;
  extracted_from: string;
  created_at?: string;
  updated_at?: string;
  notes?: string | null;
}

export interface Link {
  relation_id?: string;
  source: string;
  target: string;
  relation_type: string;
  verification: Verification;
  date?: string | null;
  amount?: number | null;
  currency?: string | null;
  property_id?: string | null;
  document_id?: string | null;
  evidence?: string | null;
  notes?: string | null;
}

export interface GraphMetadata {
  case_id: string;
  created_at: string;
  updated_at: string;
  factory_version: string;
  entity_count: number;
  relation_count: number;
  document_count: number;
  processing_stats?: Record<string, unknown>;
  verification_distribution?: Record<string, number>;
  entity_type_summary?: Record<string, number>;
  date_range?: {
    earliest_document?: string | null;
    latest_document?: string | null;
    earliest_event?: string | null;
    latest_event?: string | null;
  };
}

export interface GraphData {
  metadata: GraphMetadata;
  nodes: NodeBase[];
  links: Link[];
}
```

---

## Notes

- Frontend filters should be **relation_type-driven** (not node type labels).
- Multi-edge graphs are supported; `relation_id` distinguishes multiple links between the same nodes.
- `extracted_from` is a comma-delimited string in the export; split + trim for UI use.
- **Entity and relation types are domain-specific.** The types shown in this document are from the `cuban_property` domain. Other domains may define different types.
- The `metadata.domain` field indicates which domain configuration was used for processing.

---

## Domain-Specific Types

### Entity Types (cuban_property domain)

| Type | Description |
|------|-------------|
| `PERSON` | Individual with legal standing (owner, heir, witness, notary) |
| `PROPERTY` | Real estate asset (finca, urban property, land) |
| `ORGANIZATION` | Legal entity (bank, company, government agency) |
| `LOCATION` | Geographic entity (city, province, country) |
| `DOCUMENT` | Source document for provenance tracking |

### Relation Types (cuban_property domain)

**Ownership & Transactions:**
- `OWNS`, `OWNED` - Current/past ownership
- `SOLD`, `SOLD_TO`, `BOUGHT`, `PURCHASED_FROM` - Sales
- `INHERITED`, `CONFISCATED` - Transfers

**Family:**
- `SPOUSE_OF`, `CHILD_OF`, `HEIR_OF`, `RELATED_TO`

**Property Boundaries:**
- `BORDERS_NORTH`, `BORDERS_SOUTH`, `BORDERS_EAST`, `BORDERS_WEST`

**Documentation:**
- `MENTIONED_IN`, `WITNESSED`, `WITNESSED_BY`, `NOTARIZED`, `NOTARIZED_BY`
- `ISSUED_BY`, `REPRESENTED_BY`

**Other:**
- `EMPLOYED_BY`, `LOCATED_IN`, `REGISTERED_IN`
- `CREDITOR_OF`, `DEBTOR_OF`

See `farmer_factory/domains/configs/cuban_property/domain.yaml` for the authoritative type definitions.
