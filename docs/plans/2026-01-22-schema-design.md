# Schema Design for Civic Table Knowledge Graph

**Date:** 2026-01-22
**Status:** Approved
**Version:** 1.0

## Overview

This document defines the schema for the Civic Table knowledge graph used in the Farmer Factory processing pipeline and consumed by the Farmer Vault frontend. The schema captures entities and relations extracted from historical Cuban property documents for forensic intelligence analysis.

## Design Rationale

### Document Analysis

The schema is based on analysis of actual sample documents including:
- Handwritten and typewritten documents from 1916-1961
- Wills (testamentos abiertos)
- Property transfer documents (escrituras)
- Credit agreements and financial contracts
- Notarial certifications
- Property boundary descriptions

### Key Observations

1. **Document Quality:** Mix of typewritten and handwritten text on aged paper with varying OCR difficulty
2. **Property Boundaries Critical:** Property adjacency relationships link the ownership network
3. **Family Relationships:** Inheritance documents reveal complex family structures
4. **Document Cross-References:** Documents frequently cite other documents by number/date
5. **Financial Context:** Amounts, debts, rents provide economic context
6. **Dates and Locations:** Establish timeline and jurisdictional context

### Design Principles

1. **Core Entities Only:** Start with 5 entity types (Person, Property, Organization, Location, Document)
2. **Relations Capture Events:** Sales, inheritance, witnessing are relations, not separate entities
3. **Rich Attributes:** Entity attributes capture detailed information
4. **Flexible Formats:** Date and measurement formats accommodate historical variations
5. **Verification Mandatory:** Every entity and relation has verification metadata

## Core Schema

### Verification Tiers

Every data point in the system has an associated verification level:

```python
class VerificationTier(str, Enum):
    TIER_3_AI = "TIER_3_AI"                      # AI extracted (grey)
    TIER_2_ANALYST = "TIER_2_ANALYST"             # Civic Table verified (gold)
    TIER_2_INSTITUTIONAL = "TIER_2_INSTITUTIONAL" # Farmer House verified (gold + FH badge)
    TIER_1_CERTIFIED = "TIER_1_CERTIFIED"         # Legally certified (blue)

class Verification(BaseModel):
    tier: VerificationTier
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    verified_by: Optional[str] = None           # Analyst ID or certifying authority
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
```

**Legal Posture:** Verification tiers communicate confidence level without making legal conclusions. UI must show disclaimers for TIER_3_AI data.

### Entity Types

Five core entity types cover all information in Cuban property documents:

```python
class EntityType(str, Enum):
    PERSON = "PERSON"             # Individuals (owners, heirs, witnesses, notaries)
    PROPERTY = "PROPERTY"         # Real estate (fincas, haciendas, urban properties)
    ORGANIZATION = "ORGANIZATION" # Banks, courts, government agencies
    LOCATION = "LOCATION"         # Cities, provinces, neighborhoods, regions
    DOCUMENT = "DOCUMENT"         # Source documents (wills, contracts, certifications)
```

### Base Entity

All entities share common fields:

```python
class BaseEntity(BaseModel):
    id: str                    # Unique identifier (UUID)
    entity_type: EntityType
    verification: Verification
    extracted_from: str        # Document ID where this was first found
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
```

## Entity Definitions

### Person

Represents individuals mentioned in documents:

```python
class Person(BaseEntity):
    entity_type: Literal[EntityType.PERSON]

    # Core identity
    name: str                              # Primary name
    alternate_names: List[str] = []        # Name variations across documents

    # Demographics
    birth_date: Optional[str] = None       # Flexible date format
    death_date: Optional[str] = None
    nationality: Optional[str] = None
    residence: Optional[str] = None        # Free text or Location ID
    profession: Optional[str] = None
    marital_status: Optional[str] = None

    # Roles (what they do in documents)
    roles: List[str] = []  # e.g., ["owner", "heir", "witness", "notary"]
```

**Examples:** Mario Ceresa Rodriguez (owner, debtor), Rosalia Queral Cartaya (testator), Dr. Alberto L. Arce Padrón (notary)

### Property

Represents real estate:

```python
class Property(BaseEntity):
    entity_type: Literal[EntityType.PROPERTY]

    # Identity
    name: Optional[str] = None             # e.g., "Finca Aguaras", "Hacienda Aguaras"
    property_type: Optional[str] = None    # finca, hacienda, urban, rural

    # Location & Description
    location_id: Optional[str] = None      # Link to Location entity
    address: Optional[str] = None          # Full address text
    description: Optional[str] = None      # Physical description

    # Measurements
    area: Optional[float] = None
    area_unit: Optional[str] = None        # hectares, caballerias, etc.

    # Registry info
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None
```

**Examples:** Finca Rustica in Holguín with 20 hectares, 50 hectareas, 1 area boundaries described

### Organization

Represents institutions:

```python
class Organization(BaseEntity):
    entity_type: Literal[EntityType.ORGANIZATION]

    name: str
    org_type: Optional[str] = None  # bank, court, government, notary
    location_id: Optional[str] = None
    address: Optional[str] = None
```

**Examples:** Asociación de Crédito Rural "General Calixto Garcia", Banco de Fomento Agricola e Industrial de Cuba

### Location

Represents geographic places:

```python
class Location(BaseEntity):
    entity_type: Literal[EntityType.LOCATION]

    name: str                              # e.g., "Holguín", "Puerto Padre"
    location_type: Optional[str] = None    # city, province, neighborhood, region
    parent_location_id: Optional[str] = None  # For hierarchy (city -> province)
    country: str = "Cuba"
```

**Examples:** Holguín (city), Puerto Padre (city), Oriente (region)

### Document

Represents source documents (critical for provenance):

```python
class Document(BaseEntity):
    entity_type: Literal[EntityType.DOCUMENT]

    # Document identity
    title: Optional[str] = None
    document_type: str              # will, contract, certification, letter, etc.
    document_number: Optional[str] = None
    date: Optional[str] = None      # Document date (flexible format)

    # Provenance
    issuer: Optional[str] = None    # Person or Organization ID
    location_id: Optional[str] = None

    # Processing
    file_path: str                  # Path to original PDF
    page_count: int
    ocr_text: Optional[str] = None  # Full OCR output
    language: str = "es"            # Spanish
```

**Examples:** Last Will and Testament of Rosalia Queral Cartaya (Aug 27, 1958), Money Transfer document (Jan 4, 1961)

## Relation Types

Relations connect entities to form the knowledge graph. All relations are directed (source → target).

```python
class RelationType(str, Enum):
    # Property Ownership
    OWNS = "OWNS"                    # Person -> Property (current ownership claim)
    OWNED = "OWNED"                  # Person -> Property (historical, with date)
    INHERITED = "INHERITED"          # Person -> Property (from another person)
    SOLD_TO = "SOLD_TO"             # Person -> Person (re: a property)
    PURCHASED_FROM = "PURCHASED_FROM"  # Person -> Person (re: a property)

    # Family Relations
    SPOUSE_OF = "SPOUSE_OF"         # Person -> Person
    CHILD_OF = "CHILD_OF"           # Person -> Person
    HEIR_OF = "HEIR_OF"             # Person -> Person (legal heir designation)

    # Property Boundaries (spatial relations)
    BORDERS_NORTH = "BORDERS_NORTH"  # Property -> Property/Person
    BORDERS_SOUTH = "BORDERS_SOUTH"
    BORDERS_EAST = "BORDERS_EAST"
    BORDERS_WEST = "BORDERS_WEST"

    # Document Relations
    MENTIONED_IN = "MENTIONED_IN"    # Any Entity -> Document
    WITNESSED_BY = "WITNESSED_BY"    # Document -> Person
    NOTARIZED_BY = "NOTARIZED_BY"   # Document -> Person
    ISSUED_BY = "ISSUED_BY"          # Document -> Organization

    # Professional/Organizational
    REPRESENTED_BY = "REPRESENTED_BY"  # Person -> Person (lawyer, agent)
    EMPLOYED_BY = "EMPLOYED_BY"       # Person -> Organization

    # Financial
    CREDITOR_OF = "CREDITOR_OF"      # Person/Org -> Person (debt relationship)
    DEBTOR_OF = "DEBTOR_OF"          # Person -> Person/Org
```

### Relation Model

```python
class Relation(BaseModel):
    id: str
    type: RelationType
    source_id: str          # Entity ID
    target_id: str          # Entity ID
    verification: Verification

    # Context fields (optional, relation-specific)
    date: Optional[str] = None           # When this relation occurred
    amount: Optional[float] = None       # For financial relations
    currency: Optional[str] = None       # e.g., "pesos"
    property_id: Optional[str] = None    # For SOLD_TO/PURCHASED_FROM
    document_id: Optional[str] = None    # Source document
    notes: Optional[str] = None
```

**Key Design Decisions:**
- Relations have independent verification (can verify a relation separately from its entities)
- Directional relationships (source → target matters)
- Context fields capture relation-specific data (sale amount, date, related property)
- Border relations can point to Property OR Person (e.g., "borders with property of Juan Rodriguez")

## Graph Structure

### NetworkX Implementation

```python
class KnowledgeGraph:
    """NetworkX-based knowledge graph for entity-relation data."""

    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph
        self.metadata = GraphMetadata()

    def add_entity(self, entity: BaseEntity) -> None:
        """Add entity as node with all attributes."""
        self.graph.add_node(
            entity.id,
            entity_type=entity.entity_type.value,
            verification=entity.verification.model_dump(),
            **entity.model_dump(exclude={'id', 'entity_type', 'verification'})
        )

    def add_relation(self, relation: Relation) -> None:
        """Add relation as directed edge."""
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_id=relation.id,
            relation_type=relation.type.value,
            verification=relation.verification.model_dump(),
            **relation.model_dump(exclude={'id', 'type', 'source_id', 'target_id', 'verification'})
        )

class GraphMetadata(BaseModel):
    case_id: str
    created_at: datetime
    updated_at: datetime
    factory_version: str           # Farmer Factory version
    entity_count: int
    relation_count: int
    document_count: int
    processing_stats: Dict[str, Any] = {}  # OCR confidence, extraction stats, etc.
```

## Export Format

The Factory exports a single `graph_data.json` file consumed by the Vault frontend:

```python
class GraphExport(BaseModel):
    """Schema for graph_data.json"""

    metadata: GraphMetadata

    nodes: List[Dict[str, Any]]  # Each node = full entity with all attributes
    edges: List[Dict[str, Any]]  # Each edge = full relation

    # Computed stats for UI
    verification_summary: Dict[str, int]  # Count by tier
    entity_type_summary: Dict[str, int]   # Count by type
    date_range: Optional[Tuple[str, str]] = None  # Earliest/latest doc date
```

### Example JSON Structure

```json
{
  "metadata": {
    "case_id": "case_001",
    "created_at": "2024-01-22T10:00:00Z",
    "entity_count": 45,
    "relation_count": 78,
    "document_count": 12,
    "factory_version": "1.0.0"
  },
  "nodes": [
    {
      "id": "person_123",
      "entity_type": "PERSON",
      "name": "Mario Ceresa Rodriguez",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.92,
        "verified_by": null,
        "verified_at": null
      },
      "roles": ["owner", "debtor"],
      "extracted_from": "doc_001",
      "residence": "Holguín",
      "nationality": "Cuban"
    }
  ],
  "edges": [
    {
      "source": "person_123",
      "target": "property_456",
      "relation_type": "OWNS",
      "verification": {
        "tier": "TIER_3_AI",
        "confidence": 0.85
      },
      "date": "1960-03-26",
      "document_id": "doc_001"
    }
  ],
  "verification_summary": {
    "TIER_3_AI": 120,
    "TIER_2_ANALYST": 3,
    "TIER_2_INSTITUTIONAL": 0,
    "TIER_1_CERTIFIED": 0
  },
  "entity_type_summary": {
    "PERSON": 25,
    "PROPERTY": 12,
    "ORGANIZATION": 3,
    "LOCATION": 4,
    "DOCUMENT": 12
  }
}
```

**Key Design Decisions:**
- Single JSON file for simple deployment
- Metadata includes case_id for multi-case support in database
- Verification summary pre-computed for fast UI loading
- All attributes flattened into nodes/edges (no nested lookups needed)
- Date range helps UI show timeline context

## Schema Evolution

The schema is designed to be extensible:

**Easy to Add:**
- New entity types (e.g., Event, Transaction)
- New relation types (e.g., DONATED_TO, CONFISCATED_BY)
- New entity attributes (backward compatible)

**Process for Adding Entity Types:**
1. Add to `EntityType` enum in `structure/schema.py`
2. Create Pydantic model inheriting from `BaseEntity`
3. Update extraction prompts in `config/prompts/`
4. Add TypeScript type in `farmer_vault/lib/types.ts`
5. Add UI visualization (color, icon) in frontend config

**Process for Adding Relation Types:**
1. Add to `RelationType` enum
2. Update relation extraction prompts
3. Add TypeScript type
4. Update frontend edge rendering if needed

## Implementation Files

This design will be implemented across:

**Python (Factory):**
- `farmer_factory/structure/schema.py` - Pydantic models
- `farmer_factory/structure/graph.py` - NetworkX graph operations
- `farmer_factory/export/exporter.py` - JSON export logic

**TypeScript (Vault):**
- `farmer_vault/lib/types.ts` - TypeScript interfaces matching Pydantic models
- `farmer_vault/lib/graph-utils.ts` - Graph manipulation utilities

## Validation Rules

All entities and relations must pass validation:

1. **IDs:** Must be unique UUIDs
2. **Verification:** All entities/relations must have verification object
3. **Confidence:** Must be 0.0-1.0
4. **References:** All IDs referenced in relations must exist as entities
5. **Dates:** Flexible string format but must be parseable
6. **Required Fields:** Name for Person, document_type for Document, etc.

## Legal Compliance

The schema enforces legal posture constraints:

1. **No Legal Conclusions:** Schema has no fields like "legal_owner" or "valid_claim"
2. **Verification Required:** Every data point has verification metadata
3. **Provenance Tracking:** All entities link back to source documents
4. **Confidence Scores:** Explicit uncertainty quantification
5. **Audit Trail:** created_at, updated_at, verified_at timestamps

## Next Steps

1. Implement Pydantic models in `farmer_factory/structure/schema.py`
2. Create TypeScript types in `farmer_vault/lib/types.ts`
3. Build NetworkX graph operations in `farmer_factory/structure/graph.py`
4. Implement JSON export in `farmer_factory/export/exporter.py`
5. Test with sample documents

---

*This design was validated against real historical Cuban property documents from 1916-1961 including wills, property transfers, credit agreements, and notarial certifications.*
