# Farmer House Forensic Intelligence Platform — LLM Prompts Specification

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.3.0
> **Last Updated:** 2026-01-27
> **Status:** Zero-shot prompts (production)

---

## Overview

This document defines all LLM prompts used in Zone A (The Factory) for entity extraction, relation extraction, and document summarization. All prompts are designed for use with Anthropic's Claude API.

**Critical Principle:** All prompts extract **Forensic Facts** — what the document says. They do NOT make legal conclusions, claim assessments, or strategic recommendations.

---

## Prompt Strategy: Zero-Shot (Default)

As of v1.4.0, the extraction module uses **zero-shot prompts** exclusively:

- **More effective:** A/B testing showed zero-shot extracted 6x more entities
- **~50% cheaper:** Shorter prompts = fewer input tokens
- **Based on research:** Chilean KG paper (arXiv:2408.11975) methodology

The few-shot prompts are kept in `farmer_factory/extract/prompts/few_shot.py` for reference but are not used by the extraction service.

**Prompt files:**
```
farmer_factory/extract/prompts/
├── helpers.py      # Domain-aware helper functions
├── zero_shot.py    # Zero-shot prompts (cleanup + extraction, used by LLMExtractionService)
└── few_shot.py     # Few-shot prompts (kept for reference)
```

---

## Prompt Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROMPT PIPELINE                              │
│                                                                     │
│   OCR Text ─────────────────────────────────────────────────────┐  │
│       │                                                          │  │
│       ▼                                                          │  │
│   ┌──────────────┐                                               │  │
│   │  OCR TEXT    │──▶ Fix broken words, remove artifacts,        │  │
│   │  CLEANUP     │    restore paragraphs (preserves language)    │  │
│   └──────────────┘                                               │  │
│       │                                                          │  │
│       ▼  (cleaned text used for all downstream steps)            │  │
│   ┌──────────────┐                                               │  │
│   │   ENTITY     │──▶ Persons, Properties, Organizations,        │  │
│   │   EXTRACTION │    Locations, Dates                           │  │
│   └──────────────┘                                               │  │
│       │                                                          │  │
│       ▼                                                          │  │
│   ┌──────────────┐                                               │  │
│   │  RELATION    │──▶ Owns, Sold, Inherited, Confiscated,        │  │
│   │  EXTRACTION  │    Witnessed, etc.                            │  │
│   └──────────────┘                                               │  │
│       │                                                          │  │
│       ▼                                                          │  │
│   ┌──────────────┐                                               │  │
│   │  DOCUMENT    │──▶ Plain language summary                     │  │
│   │  SUMMARY     │    (non-legal, factual)                       │  │
│   └──────────────┘                                               │  │
│       │                                                          │  │
│       │ (All documents processed)                                │  │
│       ▼                                                          │  │
│   ┌──────────────┐                                               │  │
│   │ COREFERENCE  │──▶ "Don Mario" = "Mario Ceresa"               │  │
│   │ RESOLUTION   │    (Batch: All entities across all docs)      │  │
│   └──────────────┘                                               │  │
│       │                                                          │  │
│       │ (Graph constructed)                                      │  │
│       ▼                                                          │  │
│   ┌──────────────┐                                               │  │
│   │     GAP      │──▶ Missing evidence, broken chains            │  │
│   │  DETECTION   │    (Runs on complete graph)                   │  │
│   └──────────────┘                                               │  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Prompt Execution Timing

| Prompt | Scope | When | Input Size | Model |
|--------|-------|------|------------|-------|
| **OCR Text Cleanup** | Per document | Immediately after OCR | Raw OCR text | Haiku |
| **Entity Extraction** | Per document | After OCR cleanup | Cleaned text | Haiku |
| **Relation Extraction** | Per document | After entity extraction | Entities + cleaned text | Haiku |
| **Document Summary** | Per document | After relations | Entities + relations + OCR | Haiku |
| **Coreference Resolution** | Batch (all docs) | After all docs processed | All extracted entities | Sonnet |
| **Gap Detection** | Graph-wide | After graph construction | Complete graph + metadata | Sonnet |

**Rationale:**
- Per-document prompts use Haiku (fast, cheap) for straightforward extraction
- Batch prompts use Sonnet (better reasoning) for complex deduplication and analysis
- Coreference waits for all docs to avoid premature merging
- Gap detection runs last to identify holes in complete evidence picture

**Retry Strategy:**
- If entity/relation extraction confidence <0.60, retry with Sonnet
- If coreference produces >20% ambiguous clusters, retry with stricter threshold
- Gap detection does not retry (human review instead)

---

## System Context (Shared Across All Prompts)

This context is prepended to all extraction prompts:

```
You are a forensic document analyst working on historical property records from pre-revolutionary Cuba (pre-1959). Your task is to extract factual information from OCR-processed documents.

CRITICAL CONSTRAINTS:
1. Extract only what the document explicitly states or directly implies
2. Never make legal conclusions (e.g., "this proves ownership")
3. Never assess claim strength or litigation potential
4. Flag uncertain extractions with confidence scores
5. Preserve original Spanish names and terms
6. Note OCR quality issues that affect reliability

DOCUMENT CONTEXT:
- Most documents are in Spanish
- Many are handwritten (variable OCR quality)
- Document types include: deeds, titles, wills, confiscation decrees, registry certificates, notarial acts, correspondence
- Time period: primarily 1940s-1960s
- Geographic focus: Cuba, with emphasis on Camagüey province
```

---

## Prompt 0: OCR Text Cleanup

### Purpose
Clean noisy OCR output from degraded historical documents before entity/relation extraction. This improves both human readability and downstream extraction quality.

### Input
- Raw OCR text (typically Spanish)
- OCR confidence score
- Detected language
- Document ID

### When
Runs immediately after OCR extraction, before entity extraction. Uses Haiku (cheapest model). On failure, gracefully falls back to raw OCR text.

### Cost
~$0.0016 per document (~$0.03 for an 18-document case).

### Prompt Template

See `farmer_factory/extract/prompts/zero_shot.py` → `build_cleanup_prompt()`.

The prompt instructs the LLM to:
- Fix broken/hyphenated words across line breaks (e.g., "Far-\nmacia" → "Farmacia")
- Remove OCR noise and artifacts (random characters, reversed bleed-through text, stray symbols)
- Restore proper paragraph breaks following the document's logical sections
- Preserve the original language exactly — no translation, no paraphrasing
- Keep all names, dates, numbers, addresses, and legal terms verbatim
- Mark genuinely unreadable sections as `[ilegible]`
- Return only cleaned text (no JSON wrapper)

### Output
Plain text string — the cleaned document text. Saved to `cases/{CASE_ID}/ocr_cleaned/{doc_id}.txt` and embedded in extraction JSON at `ocr_result.cleaned_text`.

### Frontend Integration
The Vault serves cleaned text by default on the OCR tab. A "Show Raw OCR" toggle lets users compare with the unprocessed version.

---

## Prompt 1: Entity Extraction (Structured Format)

### Purpose
Extract entities with **complete structured data** including biographical details and family relationships for Person entities. This replaces the old simple value/normalized format.

### Input
- OCR text (Spanish)
- Document type (if known)
- OCR quality indicator

### Prompt Template

```
<system>
You are a forensic document analyst extracting entities from historical Cuban property documents. Extract factual information only — never make legal conclusions.
</system>

<instructions>
Analyze the OCR text and extract all entities with their detailed attributes.

ENTITY TYPES:
1. PERSON - Extract biographical and family relationship data
2. PROPERTY - Extract property details
3. ORGANIZATION - Extract organization details
4. LOCATION - Extract geographic information
5. DATE - Dates mentioned in document (returned separately)
6. MONETARY_VALUE - Financial amounts (returned separately)
7. REGISTRY_REFERENCE - Registry references (returned separately)

PERSON ENTITY SCHEMA (CRITICAL - Extract ALL available fields):
{
  "entity_type": "PERSON",
  "name": "Mario Ceresa",  // Required: Full name as written
  "alternate_names": ["Don Mario Ceresa", "M. Ceresa"],  // Titles, abbreviations

  // Demographics (extract if mentioned):
  "birth_date": "1920" or "1920-03-15",  // Year or full date
  "death_date": null,
  "nationality": "Cuban",
  "residence": "Miramar, Havana",  // Where they live
  "profession": "industrialist",
  "marital_status": "married" or "casado/casada",

  // Family relationships (HIGH PRIORITY - extract from phrases):
  // Look for: "hijo de" (son of), "hija de" (daughter of)
  //          "casado con" (married to), "esposa de" (wife of)
  //          "hermano de" (brother of), "hermana de" (sister of)
  "mother": "María López de Queral",  // Mother's name
  "father": "Juan Ceresa",  // Father's name
  "spouse": "Rosa Queral",  // Spouse name (primary if multiple)
  "children": ["Mario Jr.", "Rosa Ceresa"],  // List of children
  "siblings": ["Carlos Ceresa"],  // List of siblings

  // Roles in this document:
  "roles": ["owner", "seller"],  // e.g., owner, buyer, seller, witness, notary

  // Extraction metadata:
  "confidence": 0.95,
  "context": "...hijo de Juan Ceresa y María López...",
  "notes": "Family relationships in preamble"
}

PROPERTY ENTITY SCHEMA:
{
  "entity_type": "PROPERTY",
  "name": "Central Santa Maria",
  "property_type": "sugar mill" or "ingenio",
  "location": "Florida, Camagüey",  // As text (linked later)
  "address": "Carretera Central Km 15",
  "description": "Sugar mill with 500 hectares",
  "area": 500.0,
  "area_unit": "hectares" or "caballerías",
  "registry_number": "Folio 123, Tomo V",
  "cadastral_info": "Finca 456",
  "folio_number": "123",
  "confidence": 0.90,
  "context": "...la finca Central Santa Maria...",
  "notes": null
}

ORGANIZATION ENTITY SCHEMA:
{
  "entity_type": "ORGANIZATION",
  "name": "Banco Núñez",
  "org_type": "bank" or "banco",
  "location": "Havana",
  "address": "Calle Obispo 305",
  "confidence": 0.85,
  "context": "...el Banco Núñez...",
  "notes": null
}

LOCATION ENTITY SCHEMA:
{
  "entity_type": "LOCATION",
  "name": "Florida",
  "location_type": "municipality" or "municipio",
  "parent_location": "Camagüey",  // Parent (e.g., province)
  "country": "Cuba",
  "confidence": 0.95,
  "context": "...en el municipio de Florida...",
  "notes": null
}

EXTRACTION RULES:
- Extract only what the document explicitly states
- Preserve original Spanish terms and names
- For PERSON entities, family relationships are HIGHEST PRIORITY
- If a field is not mentioned, use null or empty list []
- Don't guess or infer data not in the text

OCR QUALITY CONSIDERATIONS:
- If text is unclear, lower confidence and note in "notes"
- Common OCR errors: ñ→n, á→a, rn→m, ll→U
</instructions>

<document_metadata>
Document ID: {document_id}
Document Type: {document_type}
OCR Quality: {ocr_quality}
Language: Spanish
</document_metadata>

<ocr_text>
{ocr_text}
</ocr_text>

<output_format>
Respond with JSON in this format:
{
  "entities": [
    // Array of structured PERSON, PROPERTY, ORGANIZATION, LOCATION entities
  ],
  "dates": [
    // {value: "15 de marzo 1958", normalized: "1958-03-15", context: "..."}
  ],
  "monetary_values": [
    // {value: "$50,000", normalized: {amount: 50000, currency: "pesos"}, context: "..."}
  ],
  "registry_refs": [
    // {value: "Folio 123", normalized: "Folio 123, Tomo V", context: "..."}
  ],
  "document_date": "1958-03-15",
  "document_date_confidence": 0.90,
  "extraction_notes": "Family relationships extracted from preamble."
}
</output_format>
```

### Expected Output Schema (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class PersonExtraction(BaseModel):
    """Structured Person entity extraction."""
    entity_type: Literal["PERSON"] = "PERSON"

    # Core identity
    name: str
    alternate_names: List[str] = Field(default_factory=list)

    # Demographics
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    nationality: Optional[str] = None
    residence: Optional[str] = None
    profession: Optional[str] = None
    marital_status: Optional[str] = None

    # Family relationships (names as strings)
    mother: Optional[str] = None
    father: Optional[str] = None
    spouse: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    siblings: List[str] = Field(default_factory=list)

    # Roles
    roles: List[str] = Field(default_factory=list)

    # Extraction metadata
    confidence: float = Field(ge=0.0, le=1.0)
    context: str
    notes: Optional[str] = None

class PropertyExtraction(BaseModel):
    entity_type: Literal["PROPERTY"] = "PROPERTY"
    name: Optional[str] = None
    property_type: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    area: Optional[float] = None
    area_unit: Optional[str] = None
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    context: str
    notes: Optional[str] = None

# Similar for OrganizationExtraction, LocationExtraction...

class StructuredEntityExtractionResult(BaseModel):
    entities: List[PersonExtraction | PropertyExtraction | ...]
    dates: List[Dict] = Field(default_factory=list)
    monetary_values: List[Dict] = Field(default_factory=list)
    registry_refs: List[Dict] = Field(default_factory=list)
    document_date: Optional[str] = None
    document_date_confidence: Optional[float] = None
    extraction_notes: Optional[str] = None
```

### Key Changes from Previous Version

**Old approach (deprecated):**
- Simple value/normalized pairs
- No biographical details
- No family relationships
- Resulted in Person entities with only names

**New approach (current):**
- Structured schemas per entity type
- Full biographical data extraction
- **Family relationships** stored on Person entities (mother, father, spouse, children, siblings)
- Enables genealogical research queries without graph traversal
- LLM extracts from Spanish phrases like "hijo de Juan Ceresa y María López"

**Why family relationships on entities?**
- Documents mention family by name, not database IDs
- Makes data human-readable and queryable
- Still creates graph edges (CHILD_OF, SPOUSE_OF) for visualization
- Redundancy is intentional: fields for queries, edges for graph traversal

---

## Prompt 2: Relation Extraction

### Purpose
Extract relationships between entities, particularly ownership, transfers, and legal actions.

### Input
- OCR text (Spanish)
- Previously extracted entities
- Document type

### Prompt Template

```
<system>
You are a forensic document analyst extracting relationships from historical Cuban property documents. Extract factual relationships only — never make legal conclusions about claim validity.
</system>

<instructions>
Analyze the OCR text and the previously extracted entities to identify relationships between them.

For each relationship, provide:
1. relation_type: One of the defined types below
2. source_entity: The entity at the start of the relationship
3. target_entity: The entity at the end of the relationship
4. confidence: 0.0-1.0 based on textual evidence
5. temporal: Date or date range if applicable
6. evidence: Quote from document supporting this relationship
7. notes: Observations, caveats, or ambiguities

RELATION TYPES:
- OWNS: Person/Organization owns Property (current or historical)
- SOLD: Person sold Property to another Person (transaction)
- BOUGHT: Person bought Property from another Person
- INHERITED: Person inherited Property (from another Person)
- CONFISCATED: Government/Organization confiscated Property
- WITNESSED: Person witnessed a transaction or legal act
- NOTARIZED: Notary certified a document
- REGISTERED_IN: Property registered in a Registry
- LOCATED_IN: Property/Person located in a Location
- EMPLOYED_BY: Person employed by Organization

FAMILY RELATIONS (use specific types when clear, RELATED_TO when ambiguous):
- CHILD_OF: Person is child of another Person (from "hijo de", "hija de")
- SPOUSE_OF: Person is spouse of another Person (from "casado con", "esposa de", "esposo de")
- HEIR_OF: Person is heir of another Person (from "heredero de")
- RELATED_TO: Generic family relation when specific type is unclear

TEMPORAL INFORMATION:
- Extract start_date and end_date where applicable
- For ongoing relationships, set ongoing: true
- Use date_precision: "exact", "month", "year", "decade", or "unknown"

CRITICAL: Only extract relationships explicitly stated or directly implied by the document. Do not infer relationships that require outside knowledge.
</instructions>

<document_metadata>
Document ID: {document_id}
Document Type: {document_type}
</document_metadata>

<extracted_entities>
{entities_json}
</extracted_entities>

<ocr_text>
{ocr_text}
</ocr_text>

<output_format>
Respond with a JSON object:
{
  "relations": [
    {
      "relation_type": "OWNS",
      "source_entity": "Mario Ceresa",
      "target_entity": "Central Santa Maria",
      "confidence": 0.88,
      "temporal": {
        "start_date": "1945-01-01",
        "end_date": null,
        "ongoing": true,
        "date_precision": "year"
      },
      "evidence": "...Don Mario Ceresa, propietario del Central Santa Maria...",
      "notes": "Ownership stated but acquisition date not specified in this document"
    }
  ],
  "extraction_notes": "Document is a notarial certification of ownership."
}
</output_format>
```

### Expected Output Schema (Pydantic)

```python
class RelationType(str, Enum):
    # Property
    OWNS = "OWNS"
    SOLD = "SOLD"
    BOUGHT = "BOUGHT"
    INHERITED = "INHERITED"
    CONFISCATED = "CONFISCATED"
    # Document
    WITNESSED = "WITNESSED"
    NOTARIZED = "NOTARIZED"
    REGISTERED_IN = "REGISTERED_IN"
    # Geographic
    LOCATED_IN = "LOCATED_IN"
    EMPLOYED_BY = "EMPLOYED_BY"
    # Family
    CHILD_OF = "CHILD_OF"
    SPOUSE_OF = "SPOUSE_OF"
    HEIR_OF = "HEIR_OF"
    RELATED_TO = "RELATED_TO"

class TemporalInfo(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ongoing: bool = False
    date_precision: Literal["exact", "month", "year", "decade", "unknown"] = "unknown"

class ExtractedRelation(BaseModel):
    relation_type: RelationType
    source_entity: str
    target_entity: str
    confidence: float = Field(ge=0.0, le=1.0)
    temporal: Optional[TemporalInfo] = None
    evidence: str
    notes: Optional[str] = None

class RelationExtractionResult(BaseModel):
    relations: list[ExtractedRelation]
    extraction_notes: Optional[str] = None
```

---

## Prompt 3: Document Summary

### Purpose
Generate a plain-language summary of the document for the dossier panel.

### Input
- OCR text (Spanish)
- Extracted entities and relations
- Document type

### Prompt Template

```
<system>
You are a forensic document analyst creating plain-language summaries of historical Cuban property documents. Write factual summaries only — never make legal conclusions or assess claim strength.
</system>

<instructions>
Create a concise, factual summary of this document in English.

SUMMARY REQUIREMENTS:
1. Length: 2-4 sentences
2. Language: Plain English (translate Spanish terms)
3. Content: What the document IS and what it SAYS
4. Tone: Neutral, factual, non-legal

INCLUDE:
- Document type and date
- Key parties mentioned
- Main subject (property, transaction, etc.)
- Significant facts stated

DO NOT INCLUDE:
- Legal conclusions ("this proves...", "this establishes...")
- Claim assessments ("strong evidence of...")
- Strategic implications ("this could be used to...")
- Speculation about missing information

EXAMPLE SUMMARIES:
✓ "This 1958 notarial certificate identifies Mario Ceresa as the owner of Central Santa Maria, a sugar mill in Camagüey province. The document bears the seal of the provincial registry."

✗ "This document proves Mario Ceresa's ownership claim and would be strong evidence in any restitution proceeding."
</instructions>

<document_metadata>
Document ID: {document_id}
Document Type: {document_type}
Document Date: {document_date}
</document_metadata>

<extracted_entities>
{entities_json}
</extracted_entities>

<extracted_relations>
{relations_json}
</extracted_relations>

<ocr_text>
{ocr_text}
</ocr_text>

<output_format>
Respond with a JSON object:
{
  "summary": "This 1958 notarial certificate identifies Mario Ceresa as the owner of Central Santa Maria, a sugar mill located in Florida municipality, Camagüey province. The document is signed by notary public José Fernández and includes two witnesses.",
  "document_classification": "ownership_certificate",
  "key_facts": [
    "Mario Ceresa identified as property owner",
    "Property: Central Santa Maria (sugar mill)",
    "Location: Florida, Camagüey",
    "Notarized by José Fernández"
  ],
  "flags": []
}
</output_format>
```

### Expected Output Schema (Pydantic)

```python
class DocumentSummaryResult(BaseModel):
    summary: str = Field(max_length=500)
    document_classification: str
    key_facts: list[str]
    flags: list[str] = Field(
        default_factory=list,
        description="Warnings: OCR issues, illegible sections, contradictions"
    )
```

---

## Prompt 4: Coreference Resolution

### Purpose
Identify entities that refer to the same real-world entity across documents.

### Input
- List of extracted entities from ALL processed documents (batch operation)
- Context snippets for each
- Temporal metadata (dates when entities appear)

### Execution Timing
**When:** After all documents have been processed through entity extraction
**Why:** Need complete entity set to avoid premature merging
**Model:** Claude Sonnet (better reasoning for ambiguous cases)

### Prompt Template

```
<system>
You are a forensic document analyst performing entity resolution on historical Cuban property records. Your task is to identify which extracted entities refer to the same real-world person, property, or organization across {document_count} documents.

This is a CRITICAL step - incorrect merging creates false connections in ownership chains. Be conservative.
</system>

<instructions>
Analyze the following list of extracted entities and identify clusters that likely refer to the same real-world entity.

CONFIDENCE THRESHOLDS (use these to guide your matching):
- ≥0.95: Auto-merge (exact match with overlapping context)
- 0.85-0.94: High confidence (title variations, known abbreviations)
- 0.70-0.84: Medium confidence (fuzzy match + supporting evidence)
- <0.70: Keep separate (ambiguous, needs human review)

MATCHING CRITERIA BY ENTITY TYPE:

**PERSON:**
- Exact name match + overlapping temporal context → 0.95
- Name with title variation ("Mario Ceresa" vs "Don Mario Ceresa") → 0.90
- Abbreviation + same property references ("M. Ceresa" with same properties) → 0.85
- Common name (e.g., "José Fernández") with no distinguishing context → 0.60 (flag for review)

**PROPERTY:**
- Name match + same municipality → 0.95
- "Central X" vs "Ingenio X" (same location) → 0.90
- Name match but no location data → 0.70 (flag for review)

**ORGANIZATION:**
- Full name vs standard abbreviation ("INRA" = "Instituto Nacional de Reforma Agraria") → 0.95
- Similar names but different time periods → Keep separate

TEMPORAL OVERLAP REQUIREMENT:
- Entities must exist in overlapping time periods to be same entity
- Exception: Inherited properties (son appears after father's death)

COMMON SPANISH NAME VARIATIONS:
- Titles: Don, Doña, Sr., Sra., Dr. (ignore for matching)
- Diminutives: Mario → Marito, José → Pepe, María → Marita
- Compound names: José María → J.M., María del Carmen → Maricarmen
- Surnames: "de" can be omitted (María de los Angeles = María Angeles)

PROPERTY NAME VARIATIONS:
- "Central X" = "Ingenio X" (both mean sugar mill)
- "Finca X" = "Colonia X" (if same location)
- "Hacienda" = large estate
- "Sitio" = small plot

GEOGRAPHIC BONUS:
- If entities share same municipality +0.05 to confidence
- If in different provinces -0.10 to confidence (likely different entities)

BE CONSERVATIVE:
- Only cluster entities with confidence ≥0.70
- If uncertain, output as "ambiguous" cluster and flag for human review
- Better to keep separate than create false merge

<entities>
{entities_json}
</entities>

<output_format>
Respond with a JSON object:
{
  "clusters": [
    {
      "cluster_id": "PERSON-001",
      "entity_type": "PERSON",
      "canonical_form": "Mario Ceresa",
      "variants": [
        {"form": "Don Mario Ceresa", "source_doc": "DOC-001"},
        {"form": "M. Ceresa", "source_doc": "DOC-003"},
        {"form": "Mario C.", "source_doc": "DOC-007"}
      ],
      "confidence": 0.95,
      "evidence": "Same family name, consistent property associations, temporal overlap"
    }
  ],
  "unresolved": [
    {
      "entity": "José Fernández",
      "reason": "Common name, insufficient context to distinguish individuals"
    }
  ]
}
</output_format>
```

---

## Prompt 5: Gap Detection

### Purpose
Identify missing evidence and incomplete chains in the document set.

### Input
- Complete graph of entities and relations
- List of all processed documents
- Timeline of extracted events

### Execution Timing
**When:** After graph construction is complete
**Why:** Need full picture of evidence to identify what's missing
**Model:** Claude Sonnet (requires complex reasoning across entire dataset)

### Minimum Evidence Thresholds

Gaps are flagged when evidence falls below these thresholds:

| Claim Type | Min Sources | Min Tier | Gap if Below |
|------------|-------------|----------|--------------|
| Property ownership | 2 documents | Any | MISSING_TRANSFER |
| Ownership transfer | 1 document | TIER_2_ANALYST or higher | UNVERIFIED_CLAIM |
| Confiscation | 1 decree | Any | HIGH priority if missing |
| Death date | 1 document | Any | Flag if timeline depends on it |
| Property valuation | 1 document | TIER_2_ANALYST or higher | MEDIUM priority |

### Prompt Template

```
<system>
You are a forensic document analyst reviewing a property claims dossier for the Farmer House Forensic Intelligence Platform. Your task is to identify gaps in the documentary evidence — missing documents, unverified claims, and incomplete ownership chains.

You are analyzing {entity_count} entities and {link_count} relations from {document_count} documents.
</system>

<instructions>
Analyze the entity graph and identify evidentiary gaps using the criteria below.

AUTOMATIC GAP TRIGGERS:
1. Any OWNS relation supported by only 1 source → Flag as UNVERIFIED_CLAIM
2. Ownership transfer (person A→B) with no SOLD/INHERITED relation → MISSING_TRANSFER
3. Property appears in multiple time periods with different owners but no transfer docs → INCOMPLETE_CHAIN
4. Critical event (death, confiscation) with precision="unknown" → UNDATED_EVENT
5. Same fact stated differently in 2+ docs (dates differ by >acceptable variance) → CONTRADICTORY_EVIDENCE

GAP TYPES:
1. **MISSING_TRANSFER**: Ownership change without supporting transfer document
   - Example: "Property owned by A in 1950, by B in 1960, no deed found"

2. **UNVERIFIED_CLAIM**: Claim supported by only one source (needs corroboration)
   - Example: "Only one document mentions this property ownership"

3. **INCOMPLETE_CHAIN**: Break in ownership timeline
   - Example: "Owner in 1945, then confiscated in 1960, but 15-year gap"

4. **UNDATED_EVENT**: Event without clear date
   - Example: "Purchase mentioned but no date given"

5. **CONTRADICTORY_EVIDENCE**: Documents that conflict
   - Example: "Doc A says sold 1958-03-15, Doc B says 1958-06-20"

6. **MISSING_REGISTRATION**: Property ownership not confirmed in official registry
   - Example: "No registry certificate found despite ownership claims"

7. **SINGLE_SOURCE_CONFISCATION**: Confiscation with no corroborating evidence
   - Example: "Only government decree, no registry annotation or correspondence"

For each gap:
1. gap_type: Type from above
2. description: Clear explanation of what's missing (2-3 sentences)
3. related_entities: Node IDs affected by this gap
4. priority: CRITICAL, HIGH, MEDIUM, LOW (use criteria below)
5. suggested_sources: Specific archives/records to search

PRIORITY CRITERIA:
- **CRITICAL**: Breaks chain of title entirely (no path from origin to current state)
- **HIGH**: Significant gap that weakens documentation (missing key transfer, conflicting dates)
- **MEDIUM**: Missing corroboration for a supported claim (single source for important fact)
- **LOW**: Nice-to-have documentation (additional corroboration for well-supported claim)

SUGGESTED SOURCES (be specific):
- "Camagüey Provincial Property Registry (Registro de la Propiedad)"
- "Notary archives in {municipality} municipality"
- "FCSC (Foreign Claims Settlement Commission) case files"
- "Cuban National Archive (Archivo Nacional de Cuba)"
- "Family correspondence or personal records"

DO NOT:
- Assess legal implications of gaps ("this gap means the claim will fail")
- Predict litigation outcomes ("you need this document to win")
- Recommend legal strategy ("hire a lawyer in Cuba")
- Flag minor omissions in well-documented chains

FOCUS ON:
- Ownership chain completeness
- Evidentiary strength of key claims
- Temporal consistency
- Corroboration levels
</instructions>

<graph_data>
{graph_json}
</graph_data>

<output_format>
Respond with a JSON object:
{
  "gaps": [
    {
      "gap_id": "GAP-001",
      "gap_type": "MISSING_TRANSFER",
      "description": "No document found showing how Mario Ceresa acquired Central Santa Maria. Documents show ownership as of 1945 but no deed of sale, inheritance filing, or transfer record.",
      "related_entities": ["PERSON-001", "PROP-001"],
      "priority": "HIGH",
      "suggested_sources": [
        "Camagüey Provincial Property Registry",
        "Notary archives in Florida municipality",
        "Family correspondence or records"
      ]
    }
  ],
  "analysis_notes": "Ownership chain has one significant gap (acquisition). Post-confiscation documentation is complete."
}
</output_format>
```

---

## Prompt Configuration

### API Parameters

```python
# config/settings.py

LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",  # Balance of speed and quality
    "max_tokens": 4096,
    "temperature": 0.1,  # Low temperature for factual extraction
    "top_p": 0.95,
}

# For complex documents or when high precision needed
LLM_CONFIG_HIGH_PRECISION = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 8192,
    "temperature": 0.0,  # Deterministic
    "top_p": 1.0,
}
```

### Prompt Versioning

All prompts include version tracking:

```python
PROMPT_VERSIONS = {
    "entity_extraction": "1.0.0",
    "relation_extraction": "1.0.0",
    "document_summary": "1.0.0",
    "coreference_resolution": "1.0.0",
    "gap_detection": "1.0.0",
}
```

Version changes are logged in the audit trail for reproducibility.

---

## Error Handling

### Retry Logic

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 2,
    "retry_on": ["rate_limit", "timeout", "server_error"],
}
```

### Validation

All LLM outputs are validated against Pydantic schemas before being accepted. Invalid outputs trigger:
1. Log the error
2. Retry with explicit schema reminder in prompt
3. If still failing, flag for human review

### Fallback Prompts

If primary extraction fails, use simplified fallback:

```
Extract only the following from this document:
1. All person names
2. All property names
3. All dates
4. All monetary amounts

Return as simple JSON lists.
```

---

## Testing

### Prompt Testing Protocol

1. **Golden Set**: Maintain 20+ manually annotated documents
2. **Precision/Recall**: Measure against golden set
3. **Regression Testing**: Run on golden set before deploying prompt changes
4. **Edge Cases**: Test with:
   - Very poor OCR quality
   - Mixed handwritten/typed
   - Multiple languages
   - Incomplete documents

### Quality Metrics

```python
QUALITY_THRESHOLDS = {
    "entity_precision": 0.85,
    "entity_recall": 0.80,
    "relation_precision": 0.80,
    "relation_recall": 0.75,
    "coreference_f1": 0.85,
}
```

---

*All prompts in this document are designed to produce Forensic Facts. They must never be modified to produce legal conclusions, claim assessments, or strategic recommendations.*
