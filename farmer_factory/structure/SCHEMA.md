# Farmer House Forensic Intelligence Platform — JSON Schema Specification

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.2.0
> **Last Updated:** 2026-01-25
> **Status:** MVP1 Target Schema (with family relationships)

---

## Overview

This document defines the JSON schema for `graph_data.json`, the primary output of Zone A (The Factory) that is consumed by Zone B (The Vault) for rendering.

The schema is designed to:
1. Capture all forensic facts with provenance
2. Enforce the Verification Triad at the data level
3. Support the Obsidian-style knowledge graph visualization
4. Enable future legal discovery and audit requirements

---

## Root Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["case_metadata", "nodes", "links"],
  "properties": {
    "case_metadata": { "$ref": "#/$defs/CaseMetadata" },
    "nodes": {
      "type": "array",
      "items": { "$ref": "#/$defs/Node" }
    },
    "links": {
      "type": "array",
      "items": { "$ref": "#/$defs/Link" }
    },
    "timeline": {
      "type": "array",
      "items": { "$ref": "#/$defs/TimelineEvent" }
    },
    "gaps": {
      "type": "array",
      "items": { "$ref": "#/$defs/Gap" }
    },
    "audit_trail": { "$ref": "#/$defs/AuditTrail" }
  }
}
```

---

## Case Metadata

```json
{
  "$defs": {
    "CaseMetadata": {
      "type": "object",
      "required": ["id", "title", "status", "created_at", "legal_disclaimer"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[A-Z]+-[0-9]+$",
          "description": "Unique case identifier (e.g., CERESA-001)"
        },
        "title": {
          "type": "string",
          "description": "Human-readable case title"
        },
        "status": {
          "type": "string",
          "enum": [
            "INTAKE",
            "PROCESSING",
            "REVIEW",
            "PILOT_ACTIVE",
            "LITIGATION_READY",
            "ARCHIVED"
          ]
        },
        "created_at": {
          "type": "string",
          "format": "date-time"
        },
        "last_verified": {
          "type": "string",
          "format": "date-time",
          "description": "Timestamp of most recent human verification"
        },
        "analyst_notes": {
          "type": "string",
          "description": "General notes about the case"
        },
        "legal_disclaimer": {
          "type": "string",
          "description": "REQUIRED legal disclaimer text"
        },
        "document_count": {
          "type": "integer",
          "minimum": 0
        },
        "page_count": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

### Example

```json
{
  "case_metadata": {
    "id": "CERESA-001",
    "title": "Ceresa Family Documentary Recovery",
    "status": "PILOT_ACTIVE",
    "created_at": "2025-01-21T00:00:00Z",
    "last_verified": null,
    "analyst_notes": "Founding case for method demonstration. 300 documents, primarily handwritten.",
    "legal_disclaimer": "This dossier presents forensic facts derived from documentary evidence. It does not constitute legal advice, and no attorney-client relationship is created. Verification tiers indicate confidence levels, not legal admissibility.",
    "document_count": 300,
    "page_count": 847
  }
}
```

---

## Verification Object

The Verification Triad is enforced via this reusable object:

```json
{
  "$defs": {
    "Verification": {
      "type": "object",
      "required": ["tier", "confidence"],
      "properties": {
        "tier": {
          "type": "string",
          "enum": ["TIER_3_AI", "TIER_2_ANALYST", "TIER_2_INSTITUTIONAL", "TIER_1_CERTIFIED"],
          "description": "Verification level"
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence score (0.0-1.0)"
        },
        "verified_by": {
          "type": "string",
          "description": "Analyst ID (Civic Table or Farmer House) for TIER_2_*, certifying body for TIER_1"
        },
        "verified_at": {
          "type": "string",
          "format": "date-time"
        },
        "certified_by": {
          "type": "string",
          "description": "Certifying authority (e.g., FCSC, notary)"
        },
        "certified_at": {
          "type": "string",
          "format": "date-time"
        },
        "notes": {
          "type": "string",
          "description": "Verification notes or caveats"
        }
      }
    }
  }
}
```

### Verification Rules

| Tier | Provider | Required Fields | Display |
|------|----------|-----------------|---------|
| `TIER_3_AI` | Civic Table platform (automated) | `tier`, `confidence` | Grey node, disclaimer badge |
| `TIER_2_ANALYST` | Civic Table analyst | `tier`, `confidence`, `verified_by`, `verified_at` | Gold node, "Verified" badge |
| `TIER_2_INSTITUTIONAL` | Farmer House analyst (optional) | `tier`, `confidence`, `verified_by`, `verified_at` | Gold node, "FH Verified" badge |
| `TIER_1_CERTIFIED` | External legal body | `tier`, `confidence`, `certified_by`, `certified_at` | Blue node, "Certified" badge |

### Confidence Thresholds

| Range | Interpretation | Action |
|-------|----------------|--------|
| 0.90 - 1.00 | High confidence | Display normally |
| 0.70 - 0.89 | Medium confidence | Display with caution indicator |
| 0.50 - 0.69 | Low confidence | Flag for human review |
| < 0.50 | Very low confidence | Do not display without explicit flag |

---

## Node Types

### Entity Type Taxonomy

```yaml
# taxonomies/types.yaml

entity_types:
  PERSON:
    description: "Individual human (living or deceased)"
    icon: "user"
    color_base: "#6366F1"  # Indigo
    
  ORGANIZATION:
    description: "Company, government body, registry office"
    icon: "building"
    color_base: "#8B5CF6"  # Violet
    
  PROPERTY:
    description: "Real property: land, building, mill, estate"
    icon: "home"
    color_base: "#10B981"  # Emerald
    
  DOCUMENT:
    description: "Source document in the archive"
    icon: "file-text"
    color_base: "#F59E0B"  # Amber
    
  LEGAL_ACT:
    description: "Legal action: confiscation decree, title transfer, inheritance filing"
    icon: "gavel"
    color_base: "#EF4444"  # Red
    
  REGISTRY_ENTRY:
    description: "Reference to official registry record"
    icon: "database"
    color_base: "#06B6D4"  # Cyan
    
  LOCATION:
    description: "Geographic location: province, municipality, address"
    icon: "map-pin"
    color_base: "#84CC16"  # Lime
```

### Node Schema

```json
{
  "$defs": {
    "Node": {
      "type": "object",
      "required": ["id", "label", "type", "verification", "sources"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[A-Z_]+-[0-9]+$",
          "description": "Unique node ID (e.g., PERSON-001, PROP-042)"
        },
        "label": {
          "type": "string",
          "description": "Display label for the node"
        },
        "type": {
          "type": "string",
          "enum": [
            "PERSON",
            "ORGANIZATION",
            "PROPERTY",
            "DOCUMENT",
            "LEGAL_ACT",
            "REGISTRY_ENTRY",
            "LOCATION"
          ]
        },
        "verification": {
          "$ref": "#/$defs/Verification"
        },
        "data": {
          "type": "object",
          "description": "Type-specific data (see Node Data Schemas)"
        },
        "sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "List of DOCUMENT node IDs that support this node"
        },
        "aliases": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Alternative names/spellings resolved to this entity"
        },
        "needs_review": {
          "type": "boolean",
          "default": false,
          "description": "Flag for human review queue"
        }
      }
    }
  }
}
```

---

## Node Data Schemas (Type-Specific)

### PERSON Data

```json
{
  "PersonData": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Full name as it appears in documents"
      },
      "alternate_names": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Titles, abbreviations, variations (e.g., 'Don Mario Ceresa', 'M. Ceresa')"
      },

      // Demographics
      "birth_date": {
        "type": "string",
        "description": "Birth date (YYYY-MM-DD or YYYY)"
      },
      "death_date": {
        "type": "string",
        "description": "Death date (YYYY-MM-DD or YYYY)"
      },
      "nationality": { "type": "string" },
      "residence": {
        "type": "string",
        "description": "Where they lived (e.g., 'Miramar, Havana')"
      },
      "profession": { "type": "string" },
      "marital_status": { "type": "string" },

      // Family relationships (CRITICAL for genealogical research)
      // These are stored as names (strings) not IDs for easy querying
      "mother": {
        "type": "string",
        "description": "Mother's name (e.g., 'María López de Queral')"
      },
      "father": {
        "type": "string",
        "description": "Father's name (e.g., 'Juan Ceresa')"
      },
      "spouse": {
        "type": "string",
        "description": "Spouse name (primary if multiple)"
      },
      "children": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of children's names"
      },
      "siblings": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of siblings' names"
      },

      // Roles in documents
      "roles": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["owner", "seller", "buyer", "heir", "witness", "notary", "official", "other"]
        },
        "description": "Roles this person plays in documents"
      }
    }
  }
}
```

**Important Design Decision:**
Family relationships are stored **both** as:
1. **Entity fields** (this schema) - Names as strings for easy querying
2. **Graph edges** - RELATED_TO, CHILD_OF, SPOUSE_OF relations for visualization

This redundancy is intentional:
- Fields enable fast queries like "Show me Rosalía Queral's father"
- Edges enable graph traversal and family tree visualization
- Both are extracted from document text using LLM (phrases like "hijo de", "casado con")

**Why names instead of IDs?**
- Documents mention family by name, not database IDs
- Makes data human-readable without joining
- Deduplication will merge entities with matching names
- Graph edges still use IDs for formal relationships

### PROPERTY Data

```json
{
  "PropertyData": {
    "type": "object",
    "properties": {
      "property_type": {
        "type": "string",
        "enum": [
          "sugar_mill",
          "farm",
          "ranch",
          "urban_property",
          "commercial",
          "industrial",
          "land",
          "other"
        ]
      },
      "property_name": { "type": "string" },
      "location": {
        "type": "object",
        "properties": {
          "province": { "type": "string" },
          "municipality": { "type": "string" },
          "address": { "type": "string" },
          "coordinates": {
            "type": "object",
            "properties": {
              "lat": { "type": "number" },
              "lng": { "type": "number" }
            }
          }
        }
      },
      "area": {
        "type": "object",
        "properties": {
          "value": { "type": "number" },
          "unit": {
            "type": "string",
            "enum": ["hectares", "caballerias", "acres", "square_meters"]
          }
        }
      },
      "valuation": {
        "type": "object",
        "properties": {
          "amount": { "type": "number" },
          "currency": { "type": "string" },
          "as_of_date": { "type": "string", "format": "date" }
        }
      },
      "fcsc_claim_number": {
        "type": "string",
        "description": "Foreign Claims Settlement Commission claim number if certified"
      }
    }
  }
}
```

### DOCUMENT Data

```json
{
  "DocumentData": {
    "type": "object",
    "properties": {
      "document_type": {
        "type": "string",
        "enum": [
          "deed",
          "title",
          "will",
          "inheritance_filing",
          "confiscation_decree",
          "registry_certificate",
          "notarial_act",
          "correspondence",
          "photograph",
          "map",
          "government_decree",
          "court_filing",
          "tax_record",
          "other"
        ]
      },
      "date": {
        "type": "string",
        "format": "date",
        "description": "Document date (may be approximate)"
      },
      "date_precision": {
        "type": "string",
        "enum": ["exact", "month", "year", "decade", "unknown"]
      },
      "language": {
        "type": "string",
        "default": "es"
      },
      "page_range": {
        "type": "object",
        "properties": {
          "start": { "type": "integer" },
          "end": { "type": "integer" }
        }
      },
      "ocr_quality": {
        "type": "string",
        "enum": ["excellent", "good", "partial", "poor", "failed"]
      },
      "handwritten": {
        "type": "boolean"
      },
      "file_path": {
        "type": "string",
        "description": "Relative path to source PDF"
      },
      "thumbnail_path": {
        "type": "string",
        "description": "Relative path to thumbnail image"
      },
      "ocr_text": {
        "type": "string",
        "description": "Full OCR text (may be large)"
      },
      "summary": {
        "type": "string",
        "description": "AI-generated plain language summary"
      }
    }
  }
}
```

### LEGAL_ACT Data

```json
{
  "LegalActData": {
    "type": "object",
    "properties": {
      "act_type": {
        "type": "string",
        "enum": [
          "confiscation",
          "nationalization",
          "transfer",
          "inheritance",
          "sale",
          "mortgage",
          "lease",
          "registration",
          "certification",
          "other"
        ]
      },
      "effective_date": {
        "type": "string",
        "format": "date"
      },
      "legal_basis": {
        "type": "string",
        "description": "Law or decree authorizing the act"
      },
      "issuing_authority": {
        "type": "string"
      },
      "reference_number": {
        "type": "string"
      }
    }
  }
}
```

---

## Link Types (Relations)

### Relation Type Taxonomy

```yaml
# taxonomies/types.yaml (continued)

relation_types:
  # Ownership relations
  OWNS:
    description: "Person/Org owns Property"
    source_types: [PERSON, ORGANIZATION]
    target_types: [PROPERTY]
    temporal: true
    
  OWNED_BY:
    description: "Inverse of OWNS (for bidirectional queries)"
    source_types: [PROPERTY]
    target_types: [PERSON, ORGANIZATION]
    temporal: true
    
  # Transfer relations
  SOLD:
    description: "Transfer via sale"
    source_types: [PERSON, ORGANIZATION]
    target_types: [PROPERTY]
    requires: [buyer]
    temporal: true
    
  INHERITED:
    description: "Transfer via inheritance"
    source_types: [PERSON]
    target_types: [PROPERTY]
    requires: [from_person]
    temporal: true
    
  CONFISCATED:
    description: "State confiscation/nationalization"
    source_types: [ORGANIZATION, LEGAL_ACT]
    target_types: [PROPERTY]
    temporal: true
    
  # Document relations
  REFERENCES:
    description: "Document mentions or cites another document"
    source_types: [DOCUMENT]
    target_types: [DOCUMENT]
    
  EVIDENCES:
    description: "Document provides evidence for a node"
    source_types: [DOCUMENT]
    target_types: [PERSON, PROPERTY, LEGAL_ACT]
    
  # Legal relations
  WITNESSED:
    description: "Person witnessed a legal act"
    source_types: [PERSON]
    target_types: [LEGAL_ACT, DOCUMENT]
    
  NOTARIZED:
    description: "Notary certified a document"
    source_types: [PERSON]
    target_types: [DOCUMENT]
    
  REGISTERED_IN:
    description: "Property registered in a registry"
    source_types: [PROPERTY]
    target_types: [REGISTRY_ENTRY]
    
  # Location relations
  LOCATED_IN:
    description: "Property/Person located in a place"
    source_types: [PROPERTY, PERSON, ORGANIZATION]
    target_types: [LOCATION]
```

### Link Schema

```json
{
  "$defs": {
    "Link": {
      "type": "object",
      "required": ["id", "source", "target", "label", "verification", "sources"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^LINK-[0-9]+$"
        },
        "source": {
          "type": "string",
          "description": "Source node ID"
        },
        "target": {
          "type": "string",
          "description": "Target node ID"
        },
        "label": {
          "type": "string",
          "enum": [
            "OWNS",
            "OWNED_BY",
            "SOLD",
            "INHERITED",
            "CONFISCATED",
            "REFERENCES",
            "EVIDENCES",
            "WITNESSED",
            "NOTARIZED",
            "REGISTERED_IN",
            "LOCATED_IN"
          ]
        },
        "verification": {
          "$ref": "#/$defs/Verification"
        },
        "data": {
          "type": "object",
          "description": "Relation-specific data"
        },
        "sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "DOCUMENT node IDs supporting this relation"
        },
        "temporal": {
          "type": "object",
          "properties": {
            "start_date": { "type": "string", "format": "date" },
            "end_date": { "type": "string", "format": "date" },
            "ongoing": { "type": "boolean" }
          }
        }
      }
    }
  }
}
```

---

## Temporal Conflict Resolution

When multiple documents provide different dates for the same event, resolve using this precedence hierarchy:

### Resolution Rules

| Priority | Source Type | Rationale | Example |
|----------|-------------|-----------|---------|
| 1 (Highest) | TIER_1_CERTIFIED with exact date | Legal certification authority | FCSC claim with notarized date |
| 2 | TIER_2_INSTITUTIONAL with exact date | Farmer House analyst verified against registry | Property registry certificate |
| 3 | TIER_2_ANALYST with exact date | Civic Table analyst verified | Analyst-reviewed deed |
| 4 | Notarized document (TIER_3_AI, exact) | Contemporary legal document | Deed signed by notary |
| 4 | Official government document | State-issued, may have propaganda bias | Confiscation decree |
| 5 | Private correspondence (exact date) | Firsthand account, may be imprecise | Letter mentioning event |
| 6 | TIER_3_AI with month/year precision | AI-extracted, lower precision | OCR of faded document |
| 7 (Lowest) | Inferred dates | Estimated from context | "circa 1950s" |

### Conflict Handling Workflow

```python
def resolve_temporal_conflict(dates: List[TemporalData]) -> TemporalData:
    """
    Given multiple dates for the same event, return authoritative date.

    Returns:
    - Highest priority date
    - Conflict flag if dates differ by more than acceptable variance
    - All conflicting sources for audit trail
    """
    # Sort by priority (tier, precision, source type)
    sorted_dates = sort_by_priority(dates)

    authoritative = sorted_dates[0]
    alternatives = sorted_dates[1:]

    # Check if conflict is within acceptable variance
    conflict_flag = False
    for alt in alternatives:
        variance = calculate_variance(authoritative, alt)
        if variance > get_acceptable_variance(authoritative.precision):
            conflict_flag = True
            break

    return {
        "date": authoritative.date,
        "precision": authoritative.precision,
        "source_tier": authoritative.tier,
        "has_conflict": conflict_flag,
        "alternative_dates": alternatives if conflict_flag else [],
        "resolution_method": "tier_precedence"
    }
```

### Acceptable Date Variance

| Precision | Variance Threshold | Conflict if Exceeded |
|-----------|-------------------|----------------------|
| exact | ±7 days | Yes - investigate discrepancy |
| month | ±30 days | Yes - flag for review |
| year | ±6 months | Yes - significant uncertainty |
| decade | ±2 years | No - expected imprecision |
| unknown | N/A | Cannot conflict |

### Conflict Flagging

When conflicts exceed acceptable variance:

```json
{
  "temporal": {
    "date": "1958-03-15",
    "precision": "exact",
    "has_conflict": true,
    "conflict_severity": "HIGH",
    "alternative_dates": [
      {
        "date": "1958-06-20",
        "source": "DOC-042",
        "tier": "TIER_3_AI",
        "notes": "OCR confidence 65% on date"
      },
      {
        "date": "1959-01-10",
        "source": "DOC-089",
        "tier": "TIER_3_AI",
        "notes": "Confiscation decree - may be retroactive"
      }
    ],
    "resolution_notes": "Using notarized deed date (DOC-003) as authoritative. Later dates may reflect administrative processing delays."
  }
}
```

### Special Cases

**Retroactive Confiscations:**
- Confiscation decrees often have issuance date != effective date
- Store both: `decree_date` and `effective_date`
- Use effective date for ownership chain timeline

**Death Dates:**
- Cross-reference multiple sources (death certificate, estate filing, correspondence)
- Flag if variance >30 days (unusual, requires investigation)

**Property Construction/Establishment:**
- "Central Santa Maria established 1920s" → `{date: "1925-01-01", precision: "decade"}`
- Conflicts with archival records override family oral history

---

## Entity Resolution & Deduplication

### Coreference Thresholds

When determining if two extracted entities refer to the same real-world entity:

| Entity Type | Matching Criteria | Min Confidence | Action |
|-------------|------------------|----------------|--------|
| PERSON (exact match) | Name identical, overlapping temporal context | 0.95 | Auto-merge |
| PERSON (title variation) | "Mario Ceresa" = "Don Mario Ceresa" | 0.90 | Auto-merge |
| PERSON (abbreviation) | "M. Ceresa" = "Mario Ceresa" + same property refs | 0.85 | Auto-merge |
| PERSON (common name) | "José Fernández" (multiple possible) | 0.60 | Flag for review |
| PROPERTY (name match) | "Central X" = "Ingenio X" | 0.90 | Auto-merge |
| PROPERTY (location match) | Same name + same municipality | 0.95 | Auto-merge |
| ORGANIZATION (abbrev) | "INRA" = "Instituto Nacional de Reforma Agraria" | 0.95 | Auto-merge |

### Deduplication Rules

```python
DEDUP_CONFIG = {
    "auto_merge_threshold": 0.90,  # Confidence must exceed this
    "review_queue_threshold": 0.70,  # Between this and auto_merge
    "keep_separate_threshold": 0.70,  # Below this, assume different entities

    "fuzzy_match_person": True,  # Enable Levenshtein for Spanish names
    "fuzzy_match_property": True,
    "fuzzy_match_organization": False,  # Acronyms don't fuzzy match well

    "temporal_overlap_required": True,  # Entities must exist in overlapping time periods
    "geographic_proximity_bonus": 0.05,  # +5% confidence if same municipality
}
```

### Ambiguous Entity Handling

When confidence is in review zone (0.70-0.90):

```json
{
  "entity_cluster": {
    "canonical_id": "PERSON-001",
    "canonical_form": "Mario Ceresa",
    "variants": [
      {"form": "Don Mario", "source": "DOC-001", "confidence": 0.85},
      {"form": "M. Ceresa", "source": "DOC-007", "confidence": 0.75}
    ],
    "ambiguous": false
  }
}

// vs. ambiguous case:

{
  "entity_cluster": {
    "canonical_id": "PERSON-042",
    "canonical_form": "José Fernández",
    "variants": [
      {"form": "José Fernández (notary)", "source": "DOC-012", "confidence": 0.72},
      {"form": "José Fernández (witness)", "source": "DOC-034", "confidence": 0.68}
    ],
    "ambiguous": true,
    "needs_review": true,
    "disambiguation_notes": "Common name. Need additional context (birth year, role) to determine if same person."
  }
}
```

---

## Timeline Events

```json
{
  "$defs": {
    "TimelineEvent": {
      "type": "object",
      "required": ["date", "event", "entities", "verification"],
      "properties": {
        "date": {
          "type": "string",
          "format": "date"
        },
        "date_precision": {
          "type": "string",
          "enum": ["exact", "month", "year", "decade", "unknown"]
        },
        "event": {
          "type": "string",
          "description": "Plain language event description"
        },
        "event_type": {
          "type": "string",
          "enum": [
            "acquisition",
            "sale",
            "inheritance",
            "confiscation",
            "registration",
            "death",
            "birth",
            "legal_filing",
            "other"
          ]
        },
        "entities": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Node IDs involved in the event"
        },
        "verification": {
          "type": "string",
          "enum": ["TIER_3_AI", "TIER_2_ANALYST", "TIER_2_INSTITUTIONAL", "TIER_1_CERTIFIED"]
        },
        "sources": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Gaps (Missing Evidence)

```json
{
  "$defs": {
    "Gap": {
      "type": "object",
      "required": ["id", "description", "priority"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^GAP-[0-9]+$"
        },
        "gap_type": {
          "type": "string",
          "enum": [
            "missing_transfer",
            "unverified_claim",
            "incomplete_chain",
            "undated_event",
            "single_source",
            "contradictory_evidence",
            "other"
          ]
        },
        "description": {
          "type": "string"
        },
        "related_entities": {
          "type": "array",
          "items": { "type": "string" }
        },
        "priority": {
          "type": "string",
          "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        },
        "suggested_sources": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Suggested archives or records to search"
        },
        "resolution_status": {
          "type": "string",
          "enum": ["OPEN", "IN_PROGRESS", "RESOLVED", "UNRESOLVABLE"]
        }
      }
    }
  }
}
```

---

## Audit Trail

```json
{
  "$defs": {
    "AuditTrail": {
      "type": "object",
      "required": ["processing_date", "pipeline_version"],
      "properties": {
        "processing_date": {
          "type": "string",
          "format": "date-time"
        },
        "pipeline_version": {
          "type": "string"
        },
        "documents_processed": {
          "type": "integer"
        },
        "pages_processed": {
          "type": "integer"
        },
        "entities_extracted": {
          "type": "integer"
        },
        "relations_extracted": {
          "type": "integer"
        },
        "human_verifications": {
          "type": "integer"
        },
        "gaps_identified": {
          "type": "integer"
        },
        "processing_log": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "timestamp": { "type": "string", "format": "date-time" },
              "action": { "type": "string" },
              "input_hash": { "type": "string" },
              "output_hash": { "type": "string" },
              "operator": { "type": "string" },
              "details": { "type": "object" }
            }
          }
        }
      }
    }
  }
}
```

---

## Schema Validation Rules

All `graph_data.json` outputs must pass these validation checks before export:

### Structural Validation

```python
class GraphDataValidator:
    """Validates graph_data.json against schema and business rules."""

    def validate(self, graph_data: GraphData) -> ValidationResult:
        errors = []
        warnings = []

        # Required fields
        if not graph_data.case_metadata:
            errors.append("Missing case_metadata")

        if len(graph_data.nodes) == 0:
            errors.append("Graph has no nodes")

        # Node validation
        node_ids = {node.id for node in graph_data.nodes}
        for node in graph_data.nodes:
            # Verify node references in sources exist
            for source_id in node.sources:
                if source_id not in node_ids:
                    errors.append(f"Node {node.id} references non-existent source {source_id}")

            # Confidence bounds
            if not (0.0 <= node.verification.confidence <= 1.0):
                errors.append(f"Node {node.id} has invalid confidence: {node.verification.confidence}")

            # Tier-specific requirements
            if node.verification.tier in ["TIER_2_ANALYST", "TIER_2_INSTITUTIONAL"]:
                if not node.verification.verified_by:
                    errors.append(f"Node {node.id} is TIER_2 but missing verified_by")

        # Link validation
        for link in graph_data.links:
            # Source and target must exist
            if link.source not in node_ids:
                errors.append(f"Link {link.id} has invalid source: {link.source}")
            if link.target not in node_ids:
                errors.append(f"Link {link.id} has invalid target: {link.target}")

            # No self-loops
            if link.source == link.target:
                warnings.append(f"Link {link.id} is a self-loop (source==target)")

        # Orphan detection
        connected_nodes = set()
        for link in graph_data.links:
            connected_nodes.add(link.source)
            connected_nodes.add(link.target)

        orphan_nodes = node_ids - connected_nodes
        orphan_pct = len(orphan_nodes) / len(graph_data.nodes) if graph_data.nodes else 0

        if orphan_pct > 0.10:
            warnings.append(f"{len(orphan_nodes)} orphan nodes ({orphan_pct:.1%}) - exceeds 10% threshold")

        # Timeline validation
        if graph_data.timeline:
            for event in graph_data.timeline:
                # Verify entity references
                for entity_id in event.entities:
                    if entity_id not in node_ids:
                        errors.append(f"Timeline event references non-existent entity: {entity_id}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### Quality Metrics

Computed automatically and stored in `audit_trail`:

```python
QUALITY_METRICS = {
    "avg_node_confidence": float,  # Mean confidence across all nodes
    "avg_link_confidence": float,  # Mean confidence across all links
    "tier_3_percentage": float,     # % of nodes that are unverified
    "entity_type_distribution": dict,  # Count by entity type
    "orphan_node_count": int,       # Nodes with no links
    "graph_density": float,         # edges / max_possible_edges
    "avg_sources_per_node": float,  # Mean supporting documents
    "temporal_coverage": dict,      # Earliest and latest dates
}
```

### Export Blockers

These conditions prevent export until resolved:

| Condition | Severity | Resolution |
|-----------|----------|------------|
| Missing required fields | ERROR | Add missing data |
| Invalid node/link references | ERROR | Fix referential integrity |
| Confidence out of bounds | ERROR | Recalculate confidence scores |
| Zero nodes in graph | ERROR | Processing failed, investigate |
| >50% orphan nodes | WARNING | Review entity extraction quality |
| Avg confidence <0.50 | WARNING | Consider manual review |
| No TIER_2+ nodes (MVP2+) | WARNING | Requires verification workflow |

---

## Complete Example

```json
{
  "case_metadata": {
    "id": "CERESA-001",
    "title": "Ceresa Family Documentary Recovery",
    "status": "PILOT_ACTIVE",
    "created_at": "2025-01-21T00:00:00Z",
    "last_verified": null,
    "analyst_notes": "Founding case for method demonstration",
    "legal_disclaimer": "This dossier presents forensic facts, not legal advice.",
    "document_count": 300,
    "page_count": 847
  },
  "nodes": [
    {
      "id": "PERSON-001",
      "label": "Mario Ceresa",
      "type": "PERSON",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.92,
        "notes": "Name extracted from 5 documents with consistent spelling"
      },
      "data": {
        "given_name": "Mario",
        "family_name": "Ceresa",
        "birth_year": 1910,
        "nationality": "Cuban",
        "role": "owner"
      },
      "sources": ["DOC-001", "DOC-003", "DOC-007", "DOC-042", "DOC-089"],
      "aliases": ["Don Mario", "M. Ceresa", "Mario C."],
      "needs_review": false
    },
    {
      "id": "PROP-001",
      "label": "Central Santa Maria",
      "type": "PROPERTY",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.88,
        "notes": "Property name and location confirmed in multiple documents"
      },
      "data": {
        "property_type": "sugar_mill",
        "property_name": "Central Santa Maria",
        "location": {
          "province": "Camagüey",
          "municipality": "Florida"
        },
        "area": {
          "value": 500,
          "unit": "hectares"
        },
        "valuation": {
          "amount": 2000000,
          "currency": "USD",
          "as_of_date": "1958-01-01"
        }
      },
      "sources": ["DOC-003", "DOC-007", "DOC-CONFISCATION"],
      "aliases": ["Santa Maria Mill", "Ingenio Santa Maria"],
      "needs_review": false
    },
    {
      "id": "DOC-CONFISCATION",
      "label": "Confiscation Decree (Oct 1959)",
      "type": "DOCUMENT",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.72,
        "notes": "OCR confidence low on handwritten annotations"
      },
      "data": {
        "document_type": "confiscation_decree",
        "date": "1959-10-12",
        "date_precision": "exact",
        "language": "es",
        "page_range": { "start": 145, "end": 147 },
        "ocr_quality": "partial",
        "handwritten": true,
        "file_path": "documents/batch_03/decree_1959.pdf",
        "summary": "Government decree nationalizing Central Santa Maria under Agrarian Reform Law."
      },
      "sources": [],
      "needs_review": true
    }
  ],
  "links": [
    {
      "id": "LINK-001",
      "source": "PERSON-001",
      "target": "PROP-001",
      "label": "OWNS",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.85
      },
      "data": {},
      "sources": ["DOC-003"],
      "temporal": {
        "start_date": "1945-01-01",
        "end_date": "1959-10-12",
        "ongoing": false
      }
    },
    {
      "id": "LINK-002",
      "source": "DOC-CONFISCATION",
      "target": "PROP-001",
      "label": "CONFISCATED",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.72
      },
      "data": {
        "legal_basis": "Agrarian Reform Law",
        "issuing_authority": "INRA"
      },
      "sources": ["DOC-CONFISCATION"],
      "temporal": {
        "start_date": "1959-10-12"
      }
    }
  ],
  "timeline": [
    {
      "date": "1945-01-01",
      "date_precision": "year",
      "event": "Mario Ceresa acquires Central Santa Maria",
      "event_type": "acquisition",
      "entities": ["PERSON-001", "PROP-001"],
      "verification": "TIER_3_AI",
      "sources": ["DOC-003"]
    },
    {
      "date": "1959-10-12",
      "date_precision": "exact",
      "event": "Central Santa Maria confiscated under Agrarian Reform Law",
      "event_type": "confiscation",
      "entities": ["PROP-001", "DOC-CONFISCATION"],
      "verification": "TIER_3_AI",
      "sources": ["DOC-CONFISCATION"]
    }
  ],
  "gaps": [
    {
      "id": "GAP-001",
      "gap_type": "missing_transfer",
      "description": "No deed found documenting Mario Ceresa's acquisition of Central Santa Maria. Current evidence shows ownership as of 1945 but not the transfer.",
      "related_entities": ["PERSON-001", "PROP-001"],
      "priority": "HIGH",
      "suggested_sources": [
        "Camagüey Provincial Registry",
        "Notary archives (Florida municipality)",
        "Family correspondence"
      ],
      "resolution_status": "OPEN"
    }
  ],
  "audit_trail": {
    "processing_date": "2025-01-21T14:30:00Z",
    "pipeline_version": "0.1.0",
    "documents_processed": 47,
    "pages_processed": 142,
    "entities_extracted": 23,
    "relations_extracted": 31,
    "human_verifications": 0,
    "gaps_identified": 3
  }
}
```

---

## TypeScript Types (for Vault Frontend)

```typescript
// lib/types.ts

export type VerificationTier = 'TIER_3_AI' | 'TIER_2_ANALYST' | 'TIER_2_INSTITUTIONAL' | 'TIER_1_CERTIFIED';

export interface Verification {
  tier: VerificationTier;
  confidence: number;
  verified_by?: string;
  verified_at?: string;
  certified_by?: string;
  certified_at?: string;
  notes?: string;
}

export type EntityType = 
  | 'PERSON' 
  | 'ORGANIZATION' 
  | 'PROPERTY' 
  | 'DOCUMENT' 
  | 'LEGAL_ACT' 
  | 'REGISTRY_ENTRY' 
  | 'LOCATION';

export interface Node {
  id: string;
  label: string;
  type: EntityType;
  verification: Verification;
  data: Record<string, any>;
  sources: string[];
  aliases?: string[];
  needs_review?: boolean;
}

export type RelationType =
  | 'OWNS'
  | 'OWNED_BY'
  | 'SOLD'
  | 'INHERITED'
  | 'CONFISCATED'
  | 'REFERENCES'
  | 'EVIDENCES'
  | 'WITNESSED'
  | 'NOTARIZED'
  | 'REGISTERED_IN'
  | 'LOCATED_IN';

export interface Link {
  id: string;
  source: string;
  target: string;
  label: RelationType;
  verification: Verification;
  data: Record<string, any>;
  sources: string[];
  temporal?: {
    start_date?: string;
    end_date?: string;
    ongoing?: boolean;
  };
}

export interface TimelineEvent {
  date: string;
  date_precision?: 'exact' | 'month' | 'year' | 'decade' | 'unknown';
  event: string;
  event_type?: string;
  entities: string[];
  verification: VerificationTier;
  sources: string[];
}

export interface Gap {
  id: string;
  gap_type?: string;
  description: string;
  related_entities: string[];
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  suggested_sources?: string[];
  resolution_status?: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'UNRESOLVABLE';
}

export interface CaseMetadata {
  id: string;
  title: string;
  status: string;
  created_at: string;
  last_verified?: string;
  analyst_notes?: string;
  legal_disclaimer: string;
  document_count?: number;
  page_count?: number;
}

export interface AuditTrail {
  processing_date: string;
  pipeline_version: string;
  documents_processed: number;
  pages_processed?: number;
  entities_extracted: number;
  relations_extracted: number;
  human_verifications: number;
  gaps_identified?: number;
}

export interface GraphData {
  case_metadata: CaseMetadata;
  nodes: Node[];
  links: Link[];
  timeline?: TimelineEvent[];
  gaps?: Gap[];
  audit_trail: AuditTrail;
}
```

---

*This schema is the contract between Zone A (Factory) and Zone B (Vault). Any changes to this schema require updates to both systems.*
