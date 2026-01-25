# Structured Entity Extraction

> **Date:** 2026-01-25
> **Version:** 1.2.0
> **Status:** Active

---

## Overview

As of version 1.2.0, the platform uses **structured entity extraction** instead of simple value/normalized pairs. This enables extraction of complete biographical data and **family relationships** from historical documents.

## What Changed

### Before (v1.1.0)

Entities extracted as simple intermediate format:

```python
{
  "entity_type": "PERSON",
  "value": "Mario Ceresa",
  "normalized": "Mario Ceresa",
  "confidence": 0.95,
  "context": "...",
  "notes": "..."
}
```

**Problem:** Only captured names, no biographical details. Person entities ended up with just `name` field populated, everything else `None`.

### After (v1.2.0)

Entities extracted with complete structured schemas:

```python
{
  "entity_type": "PERSON",
  "name": "Mario Ceresa",
  "alternate_names": ["Don Mario Ceresa"],

  # Demographics
  "birth_date": "1920",
  "nationality": "Cuban",
  "residence": "Miramar, Havana",
  "profession": "industrialist",

  # Family relationships (CRITICAL for genealogical research)
  "mother": "María López de Queral",
  "father": "Juan Ceresa",
  "spouse": "Rosa Queral",
  "children": ["Mario Jr.", "Rosa Ceresa"],
  "siblings": ["Carlos Ceresa"],

  # Roles
  "roles": ["owner", "seller"],

  # Extraction metadata
  "confidence": 0.95,
  "context": "...hijo de Juan Ceresa y María López...",
  "notes": "Family relationships extracted from preamble"
}
```

## Family Relationships

### Why Store on Entity?

Family relationships are stored **both** as:

1. **Entity fields** (names as strings) - For direct queries
2. **Graph edges** (CHILD_OF, SPOUSE_OF relations) - For visualization

This redundancy is **intentional**:

- **Fields enable fast queries:** "Show me Rosalía Queral's father" → just read the field
- **Edges enable graph traversal:** Build family trees, trace lineages
- **Both extracted from document text:** LLM parses Spanish phrases like:
  - "hijo de Juan Ceresa y María López" → `father: "Juan Ceresa", mother: "María López"`
  - "casado con Rosa Queral" → `spouse: "Rosa Queral"`
  - "hermano de Carlos Ceresa" → `siblings: ["Carlos Ceresa"]`

### Why Names Instead of IDs?

Documents mention family **by name**, not database IDs:

✅ **Good:** `"father": "Juan Ceresa"` - Human-readable, matches document text
❌ **Bad:** `"father_id": "abc123"` - Requires join, not human-readable

Deduplication will merge entities with matching names, creating proper graph connections.

## Extraction Prompt Changes

### New PERSON Schema Instructions

The LLM extraction prompt now includes detailed instructions for family relationships:

```
// Family relationships (HIGH PRIORITY - extract from phrases):
// Look for: "hijo de" (son of), "hija de" (daughter of)
//          "casado con" (married to), "esposa de" (wife of)
//          "hermano de" (brother of), "hermana de" (sister of)
"mother": "María López de Queral",  // Mother's name
"father": "Juan Ceresa",  // Father's name
"spouse": "Rosa Queral",  // Spouse name (primary if multiple)
"children": ["Mario Jr.", "Rosa Ceresa"],  // List of children
"siblings": ["Carlos Ceresa"],  // List of siblings
```

### Common Spanish Phrases

The LLM is trained to recognize these patterns in historical Cuban documents:

| Spanish Phrase | Meaning | Extracts To |
|----------------|---------|-------------|
| "hijo de X y Y" | son of X and Y | `father: X, mother: Y` |
| "hija de X y Y" | daughter of X and Y | `father: X, mother: Y` |
| "casado con X" | married to X | `spouse: X` |
| "esposa de X" | wife of X | `spouse: X` (on self), also creates relation |
| "hermano de X" | brother of X | `siblings: [X]` |
| "madre de X" | mother of X | `children: [X]` (on self) |

## Implementation Files

### Core Changes

1. **`farmer_factory/extract/llm.py`**
   - Added `PersonExtraction`, `PropertyExtraction`, `OrganizationExtraction`, `LocationExtraction` models
   - Rewrote `_build_entity_prompt()` with structured extraction instructions
   - Updated `_transform_to_final_entities()` to populate all fields
   - Changed return type from `EntityExtractionResult` to `StructuredEntityExtractionResult`

2. **`farmer_factory/structure/schema.py`**
   - Added family relationship fields to `Person` class:
     ```python
     mother: Optional[str] = None
     father: Optional[str] = None
     spouse: Optional[str] = None
     children: List[str] = Field(default_factory=list)
     siblings: List[str] = Field(default_factory=list)
     ```

### Documentation Updates

1. **`.claude/PROMPTS.md`** (v1.2.0)
   - Updated Prompt 1: Entity Extraction with structured format
   - Added family relationship extraction instructions
   - Documented Spanish phrase patterns

2. **`.claude/SCHEMA.md`** (v1.2.0)
   - Updated PERSON data schema with family fields
   - Added design rationale for storing names vs IDs
   - Documented redundancy between fields and edges

## Testing

After this change, re-process documents to see:

1. ✅ Person entities with populated biographical fields
2. ✅ Family relationships extracted from document preambles
3. ✅ Better genealogical data for family tree reconstruction
4. ✅ Cleaner knowledge graph with richer entity data

## Migration Notes

**Old extractions (v1.1.0) are incompatible.** To use the new extraction:

1. Clean case outputs: `python cli.py clean CASE-ID --confirm`
2. Re-process documents: `python cli.py process CASE-ID --force-typed`
3. Train dedupe models: `python cli.py train-deduplication CASE-ID --entity-type PERSON`
4. Review extracted entities in `cases/CASE-ID/extractions/`

## Related ADRs

- **2026-01-23: Gap Detection Deferred** - Analyst workflow focus
- **2026-01-24: Replace Fuzzy Matching with Dedupe** - ML-based deduplication
- **2026-01-25: Structured Entity Extraction** - This document

---

*For implementation details, see `farmer_factory/extract/llm.py` and `.claude/PROMPTS.md`*
