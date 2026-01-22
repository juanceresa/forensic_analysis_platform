# Schema Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the Pydantic schema models, NetworkX graph operations, and JSON export logic for the Civic Table knowledge graph.

**Architecture:** Build three core modules - `schema.py` defines Pydantic models for entities and relations with validation, `graph.py` provides NetworkX-based graph operations with conflict resolution, and `exporter.py` handles JSON serialization with Supabase upload.

**Tech Stack:** Python 3.10+, Pydantic 2.5+, NetworkX 3.2+, Supabase client

---

## Task 1: Verification and Base Models

**Files:**
- Create: `farmer_factory/structure/schema.py`
- Test: `tests/structure/test_schema.py`

**Step 1: Create test directory structure**

```bash
mkdir -p tests/structure
touch tests/structure/__init__.py
```

**Step 2: Write failing tests for Verification model**

Create `tests/structure/test_schema.py`:

```python
"""Tests for schema models."""

import pytest
from datetime import datetime
from farmer_factory.structure.schema import (
    VerificationTier,
    Verification,
    EntityType,
)


def test_verification_tier_enum():
    """Test VerificationTier enum values."""
    assert VerificationTier.TIER_3_AI == "TIER_3_AI"
    assert VerificationTier.TIER_2_ANALYST == "TIER_2_ANALYST"
    assert VerificationTier.TIER_2_INSTITUTIONAL == "TIER_2_INSTITUTIONAL"
    assert VerificationTier.TIER_1_CERTIFIED == "TIER_1_CERTIFIED"


def test_verification_model_minimal():
    """Test Verification with minimal required fields."""
    verification = Verification(
        tier=VerificationTier.TIER_3_AI,
        confidence=0.85
    )
    assert verification.tier == VerificationTier.TIER_3_AI
    assert verification.confidence == 0.85
    assert verification.verified_by is None
    assert verification.verified_at is None
    assert verification.notes is None


def test_verification_model_full():
    """Test Verification with all fields."""
    now = datetime.now()
    verification = Verification(
        tier=VerificationTier.TIER_2_ANALYST,
        confidence=0.95,
        verified_by="analyst_123",
        verified_at=now,
        notes="Verified against original document"
    )
    assert verification.tier == VerificationTier.TIER_2_ANALYST
    assert verification.confidence == 0.95
    assert verification.verified_by == "analyst_123"
    assert verification.verified_at == now
    assert verification.notes == "Verified against original document"


def test_verification_confidence_range():
    """Test confidence must be between 0.0 and 1.0."""
    # Valid
    Verification(tier=VerificationTier.TIER_3_AI, confidence=0.0)
    Verification(tier=VerificationTier.TIER_3_AI, confidence=1.0)

    # Invalid - too low
    with pytest.raises(ValueError):
        Verification(tier=VerificationTier.TIER_3_AI, confidence=-0.1)

    # Invalid - too high
    with pytest.raises(ValueError):
        Verification(tier=VerificationTier.TIER_3_AI, confidence=1.1)


def test_entity_type_enum():
    """Test EntityType enum values."""
    assert EntityType.PERSON == "PERSON"
    assert EntityType.PROPERTY == "PROPERTY"
    assert EntityType.ORGANIZATION == "ORGANIZATION"
    assert EntityType.LOCATION == "LOCATION"
    assert EntityType.DOCUMENT == "DOCUMENT"
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py -v`

Expected: ImportError (module doesn't exist yet)

**Step 4: Write minimal Verification implementation**

Create `farmer_factory/structure/schema.py`:

```python
"""
Pydantic schema models for Civic Table knowledge graph.

Defines entity types, relation types, and validation rules.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class VerificationTier(str, Enum):
    """Verification tier for entities and relations."""
    TIER_3_AI = "TIER_3_AI"
    TIER_2_ANALYST = "TIER_2_ANALYST"
    TIER_2_INSTITUTIONAL = "TIER_2_INSTITUTIONAL"
    TIER_1_CERTIFIED = "TIER_1_CERTIFIED"


class Verification(BaseModel):
    """Verification metadata for entities and relations."""
    tier: VerificationTier
    confidence: float = Field(ge=0.0, le=1.0)
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


class EntityType(str, Enum):
    """Entity types in the knowledge graph."""
    PERSON = "PERSON"
    PROPERTY = "PROPERTY"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DOCUMENT = "DOCUMENT"
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/structure/ farmer_factory/structure/schema.py
git commit -m "feat: add Verification and EntityType enums

Implement verification tier system and base entity types.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Base Entity Model

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for BaseEntity**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import BaseEntity


def test_base_entity_creation():
    """Test BaseEntity creation with required fields."""
    entity = BaseEntity(
        id="test_123",
        entity_type=EntityType.PERSON,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )
    assert entity.id == "test_123"
    assert entity.entity_type == EntityType.PERSON
    assert entity.verification.tier == VerificationTier.TIER_3_AI
    assert entity.extracted_from == "doc_001"
    assert entity.notes is None


def test_base_entity_timestamps():
    """Test BaseEntity has timestamps."""
    entity = BaseEntity(
        id="test_123",
        entity_type=EntityType.PERSON,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )
    assert isinstance(entity.created_at, datetime)
    assert isinstance(entity.updated_at, datetime)


def test_base_entity_with_notes():
    """Test BaseEntity with notes field."""
    entity = BaseEntity(
        id="test_123",
        entity_type=EntityType.PERSON,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001",
        notes="Test note"
    )
    assert entity.notes == "Test note"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_base_entity_creation -v`

Expected: ImportError (BaseEntity doesn't exist)

**Step 3: Implement BaseEntity**

Add to `farmer_factory/structure/schema.py` after EntityType:

```python
class BaseEntity(BaseModel):
    """Base class for all entity types."""
    id: str
    entity_type: EntityType
    verification: Verification
    extracted_from: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py::test_base_entity -v`

Expected: All base_entity tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add BaseEntity model

Base class for all entities with verification and timestamps.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: Person Entity Model

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for Person entity**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import Person


def test_person_minimal():
    """Test Person with only required fields."""
    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.92
        ),
        extracted_from="doc_001"
    )
    assert person.name == "Mario Ceresa Rodriguez"
    assert person.alternate_names == []
    assert person.roles == []
    assert person.birth_date is None
    assert person.nationality is None


def test_person_full():
    """Test Person with all fields."""
    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        alternate_names=["Mario Ceresa", "M. Ceresa Rodriguez"],
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.95
        ),
        extracted_from="doc_001",
        birth_date="1920-05-15",
        death_date="1995-12-20",
        nationality="Cuban",
        residence="Holguín, Oriente, Cuba",
        profession="Agricultor",
        marital_status="Married",
        roles=["owner", "debtor"]
    )
    assert person.name == "Mario Ceresa Rodriguez"
    assert len(person.alternate_names) == 2
    assert person.birth_date == "1920-05-15"
    assert person.nationality == "Cuban"
    assert "owner" in person.roles


def test_person_entity_type_literal():
    """Test Person entity_type must be PERSON."""
    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Test Person",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )
    assert person.entity_type == EntityType.PERSON
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_person -v`

Expected: ImportError (Person doesn't exist)

**Step 3: Implement Person entity**

Add to `farmer_factory/structure/schema.py` after BaseEntity:

```python
class Person(BaseEntity):
    """Person entity (owners, heirs, witnesses, notaries)."""
    entity_type: Literal[EntityType.PERSON] = EntityType.PERSON

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

    # Roles
    roles: List[str] = Field(default_factory=list)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py::test_person -v`

Expected: All person tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add Person entity model

Person entity with identity, demographics, and roles.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Property, Organization, Location Entities

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for remaining entities**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import Property, Organization, Location


def test_property_minimal():
    """Test Property with minimal fields."""
    prop = Property(
        id="property_123",
        entity_type=EntityType.PROPERTY,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )
    assert prop.entity_type == EntityType.PROPERTY
    assert prop.name is None
    assert prop.property_type is None


def test_property_full():
    """Test Property with all fields."""
    prop = Property(
        id="property_123",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        property_type="finca",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001",
        location_id="loc_456",
        address="Holguín, Oriente, Cuba",
        description="Rustic property with boundaries",
        area=20.5,
        area_unit="hectares",
        registry_number="REG-1234",
        cadastral_info="CAD-5678",
        folio_number="FOLIO-90"
    )
    assert prop.name == "Finca Aguaras"
    assert prop.area == 20.5
    assert prop.area_unit == "hectares"


def test_organization_minimal():
    """Test Organization with minimal fields."""
    org = Organization(
        id="org_123",
        entity_type=EntityType.ORGANIZATION,
        name="Banco de Fomento Agricola",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90
        ),
        extracted_from="doc_001"
    )
    assert org.name == "Banco de Fomento Agricola"
    assert org.org_type is None


def test_organization_full():
    """Test Organization with all fields."""
    org = Organization(
        id="org_123",
        entity_type=EntityType.ORGANIZATION,
        name="Banco de Fomento Agricola",
        org_type="bank",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90
        ),
        extracted_from="doc_001",
        location_id="loc_456",
        address="Havana, Cuba"
    )
    assert org.org_type == "bank"
    assert org.address == "Havana, Cuba"


def test_location_minimal():
    """Test Location with minimal fields."""
    loc = Location(
        id="loc_123",
        entity_type=EntityType.LOCATION,
        name="Holguín",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.95
        ),
        extracted_from="doc_001"
    )
    assert loc.name == "Holguín"
    assert loc.country == "Cuba"
    assert loc.location_type is None


def test_location_full():
    """Test Location with hierarchy."""
    loc = Location(
        id="loc_123",
        entity_type=EntityType.LOCATION,
        name="Puerto Padre",
        location_type="city",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.95
        ),
        extracted_from="doc_001",
        parent_location_id="loc_456",
        country="Cuba"
    )
    assert loc.name == "Puerto Padre"
    assert loc.location_type == "city"
    assert loc.parent_location_id == "loc_456"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_property -v`
Run: `pytest tests/structure/test_schema.py::test_organization -v`
Run: `pytest tests/structure/test_schema.py::test_location -v`

Expected: ImportError (classes don't exist)

**Step 3: Implement Property, Organization, Location**

Add to `farmer_factory/structure/schema.py` after Person:

```python
class Property(BaseEntity):
    """Property entity (fincas, haciendas, urban properties)."""
    entity_type: Literal[EntityType.PROPERTY] = EntityType.PROPERTY

    # Identity
    name: Optional[str] = None
    property_type: Optional[str] = None

    # Location & Description
    location_id: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

    # Measurements
    area: Optional[float] = None
    area_unit: Optional[str] = None

    # Registry info
    registry_number: Optional[str] = None
    cadastral_info: Optional[str] = None
    folio_number: Optional[str] = None


class Organization(BaseEntity):
    """Organization entity (banks, courts, government agencies)."""
    entity_type: Literal[EntityType.ORGANIZATION] = EntityType.ORGANIZATION

    name: str
    org_type: Optional[str] = None
    location_id: Optional[str] = None
    address: Optional[str] = None


class Location(BaseEntity):
    """Location entity (cities, provinces, neighborhoods)."""
    entity_type: Literal[EntityType.LOCATION] = EntityType.LOCATION

    name: str
    location_type: Optional[str] = None
    parent_location_id: Optional[str] = None
    country: str = "Cuba"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py -v -k "property or organization or location"`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add Property, Organization, Location entities

Complete entity models for properties, organizations, and locations.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Document Entity Model

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for Document entity**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import Document


def test_document_minimal():
    """Test Document with required fields."""
    doc = Document(
        id="doc_123",
        entity_type=EntityType.DOCUMENT,
        document_type="will",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_123",
        file_path="/path/to/document.pdf",
        page_count=5
    )
    assert doc.document_type == "will"
    assert doc.file_path == "/path/to/document.pdf"
    assert doc.page_count == 5
    assert doc.language == "es"


def test_document_full():
    """Test Document with all fields."""
    doc = Document(
        id="doc_123",
        entity_type=EntityType.DOCUMENT,
        title="Last Will and Testament of Rosalia Queral Cartaya",
        document_type="will",
        document_number="357",
        date="1958-08-27",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_123",
        issuer="notary_456",
        location_id="loc_789",
        file_path="/path/to/document.pdf",
        page_count=5,
        ocr_text="Full OCR text here...",
        language="es"
    )
    assert doc.title == "Last Will and Testament of Rosalia Queral Cartaya"
    assert doc.document_number == "357"
    assert doc.date == "1958-08-27"
    assert doc.issuer == "notary_456"
    assert doc.ocr_text == "Full OCR text here..."
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_document -v`

Expected: ImportError (Document doesn't exist)

**Step 3: Implement Document entity**

Add to `farmer_factory/structure/schema.py` after Location:

```python
class Document(BaseEntity):
    """Document entity (source documents for provenance)."""
    entity_type: Literal[EntityType.DOCUMENT] = EntityType.DOCUMENT

    # Document identity
    title: Optional[str] = None
    document_type: str
    document_number: Optional[str] = None
    date: Optional[str] = None

    # Provenance
    issuer: Optional[str] = None
    location_id: Optional[str] = None

    # Processing
    file_path: str
    page_count: int
    ocr_text: Optional[str] = None
    language: str = "es"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py::test_document -v`

Expected: All document tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add Document entity model

Document entity for source provenance tracking.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Relation Types and Model

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for RelationType and Relation**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import RelationType, Relation


def test_relation_type_enum():
    """Test RelationType enum values."""
    assert RelationType.OWNS == "OWNS"
    assert RelationType.SPOUSE_OF == "SPOUSE_OF"
    assert RelationType.BORDERS_NORTH == "BORDERS_NORTH"
    assert RelationType.MENTIONED_IN == "MENTIONED_IN"


def test_relation_minimal():
    """Test Relation with minimal fields."""
    relation = Relation(
        id="rel_123",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )
    assert relation.type == RelationType.OWNS
    assert relation.source_id == "person_123"
    assert relation.target_id == "property_456"
    assert relation.date is None
    assert relation.amount is None


def test_relation_with_context():
    """Test Relation with context fields."""
    relation = Relation(
        id="rel_123",
        type=RelationType.SOLD_TO,
        source_id="person_123",
        target_id="person_456",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.95
        ),
        date="1960-03-26",
        amount=2850.50,
        currency="pesos",
        property_id="property_789",
        document_id="doc_001",
        notes="Sale documented in notarial deed"
    )
    assert relation.date == "1960-03-26"
    assert relation.amount == 2850.50
    assert relation.currency == "pesos"
    assert relation.property_id == "property_789"
    assert relation.document_id == "doc_001"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_relation -v`

Expected: ImportError (RelationType and Relation don't exist)

**Step 3: Implement RelationType and Relation**

Add to `farmer_factory/structure/schema.py` after Document:

```python
class RelationType(str, Enum):
    """Relation types in the knowledge graph."""
    # Property Ownership
    OWNS = "OWNS"
    OWNED = "OWNED"
    INHERITED = "INHERITED"
    SOLD_TO = "SOLD_TO"
    PURCHASED_FROM = "PURCHASED_FROM"

    # Family Relations
    SPOUSE_OF = "SPOUSE_OF"
    CHILD_OF = "CHILD_OF"
    HEIR_OF = "HEIR_OF"

    # Property Boundaries
    BORDERS_NORTH = "BORDERS_NORTH"
    BORDERS_SOUTH = "BORDERS_SOUTH"
    BORDERS_EAST = "BORDERS_EAST"
    BORDERS_WEST = "BORDERS_WEST"

    # Document Relations
    MENTIONED_IN = "MENTIONED_IN"
    WITNESSED_BY = "WITNESSED_BY"
    NOTARIZED_BY = "NOTARIZED_BY"
    ISSUED_BY = "ISSUED_BY"

    # Professional/Organizational
    REPRESENTED_BY = "REPRESENTED_BY"
    EMPLOYED_BY = "EMPLOYED_BY"

    # Financial
    CREDITOR_OF = "CREDITOR_OF"
    DEBTOR_OF = "DEBTOR_OF"


class Relation(BaseModel):
    """Relation between entities in the knowledge graph."""
    id: str
    type: RelationType
    source_id: str
    target_id: str
    verification: Verification

    # Context fields
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    property_id: Optional[str] = None
    document_id: Optional[str] = None
    notes: Optional[str] = None
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py::test_relation -v`

Expected: All relation tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add RelationType enum and Relation model

Complete relation types and model with context fields.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: Graph Metadata and Export Models

**Files:**
- Modify: `farmer_factory/structure/schema.py`
- Modify: `tests/structure/test_schema.py`

**Step 1: Write failing tests for metadata and export**

Append to `tests/structure/test_schema.py`:

```python
from farmer_factory.structure.schema import GraphMetadata, GraphExport


def test_graph_metadata():
    """Test GraphMetadata model."""
    metadata = GraphMetadata(
        case_id="case_001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        factory_version="1.0.0",
        entity_count=45,
        relation_count=78,
        document_count=12,
        processing_stats={"ocr_confidence": 0.85}
    )
    assert metadata.case_id == "case_001"
    assert metadata.entity_count == 45
    assert metadata.processing_stats["ocr_confidence"] == 0.85


def test_graph_export():
    """Test GraphExport model."""
    metadata = GraphMetadata(
        case_id="case_001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        factory_version="1.0.0",
        entity_count=2,
        relation_count=1,
        document_count=1
    )

    export = GraphExport(
        metadata=metadata,
        nodes=[
            {
                "id": "person_123",
                "entity_type": "PERSON",
                "name": "Test Person"
            }
        ],
        edges=[
            {
                "source": "person_123",
                "target": "property_456",
                "relation_type": "OWNS"
            }
        ],
        verification_summary={"TIER_3_AI": 3},
        entity_type_summary={"PERSON": 1, "PROPERTY": 1}
    )

    assert len(export.nodes) == 1
    assert len(export.edges) == 1
    assert export.verification_summary["TIER_3_AI"] == 3
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_schema.py::test_graph -v`

Expected: ImportError (GraphMetadata and GraphExport don't exist)

**Step 3: Implement GraphMetadata and GraphExport**

Add to `farmer_factory/structure/schema.py` at the end:

```python
class GraphMetadata(BaseModel):
    """Metadata for knowledge graph export."""
    case_id: str
    created_at: datetime
    updated_at: datetime
    factory_version: str
    entity_count: int
    relation_count: int
    document_count: int
    processing_stats: Dict[str, Any] = Field(default_factory=dict)


class GraphExport(BaseModel):
    """Export format for graph_data.json."""
    metadata: GraphMetadata
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    verification_summary: Dict[str, int]
    entity_type_summary: Dict[str, int]
    date_range: Optional[tuple[str, str]] = None
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_schema.py::test_graph -v`

Expected: All graph tests PASS

**Step 5: Run all schema tests**

Run: `pytest tests/structure/test_schema.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/structure/test_schema.py farmer_factory/structure/schema.py
git commit -m "feat: add GraphMetadata and GraphExport models

Complete schema with export format models.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: NetworkX Graph Operations

**Files:**
- Create: `farmer_factory/structure/graph.py`
- Create: `tests/structure/test_graph.py`

**Step 1: Write failing tests for KnowledgeGraph**

Create `tests/structure/test_graph.py`:

```python
"""Tests for knowledge graph operations."""

import pytest
from datetime import datetime
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification,
)


def test_knowledge_graph_init():
    """Test KnowledgeGraph initialization."""
    kg = KnowledgeGraph(case_id="case_001")
    assert kg.case_id == "case_001"
    assert kg.graph.number_of_nodes() == 0
    assert kg.graph.number_of_edges() == 0


def test_add_entity():
    """Test adding entity to graph."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)

    assert kg.graph.number_of_nodes() == 1
    assert kg.graph.has_node("person_123")
    assert kg.graph.nodes["person_123"]["name"] == "Mario Ceresa"
    assert kg.graph.nodes["person_123"]["entity_type"] == "PERSON"


def test_add_relation():
    """Test adding relation to graph."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    relation = Relation(
        id="rel_789",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(relation)

    assert kg.graph.number_of_edges() == 1
    assert kg.graph.has_edge("person_123", "property_456")
    assert kg.graph.edges["person_123", "property_456"]["relation_type"] == "OWNS"


def test_get_entity():
    """Test retrieving entity from graph."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)
    retrieved = kg.get_entity("person_123")

    assert retrieved is not None
    assert retrieved["name"] == "Mario Ceresa"
    assert retrieved["entity_type"] == "PERSON"


def test_get_nonexistent_entity():
    """Test retrieving nonexistent entity returns None."""
    kg = KnowledgeGraph(case_id="case_001")
    assert kg.get_entity("nonexistent") is None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/structure/test_graph.py -v`

Expected: ImportError (KnowledgeGraph doesn't exist)

**Step 3: Implement KnowledgeGraph**

Create `farmer_factory/structure/graph.py`:

```python
"""
Knowledge graph operations using NetworkX.

Provides graph construction, entity/relation management, and conflict resolution.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import networkx as nx

from .schema import (
    BaseEntity,
    Relation,
    GraphMetadata,
)


class KnowledgeGraph:
    """NetworkX-based knowledge graph for entity-relation data."""

    def __init__(self, case_id: str):
        """Initialize knowledge graph.

        Args:
            case_id: Unique identifier for this case
        """
        self.case_id = case_id
        self.graph = nx.DiGraph()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_entity(self, entity: BaseEntity) -> None:
        """Add entity as node with all attributes.

        Args:
            entity: Entity to add to graph
        """
        self.graph.add_node(
            entity.id,
            entity_type=entity.entity_type.value,
            verification=entity.verification.model_dump(),
            **entity.model_dump(exclude={'id', 'entity_type', 'verification'})
        )
        self.updated_at = datetime.now()

    def add_relation(self, relation: Relation) -> None:
        """Add relation as directed edge.

        Args:
            relation: Relation to add to graph

        Raises:
            ValueError: If source or target entity doesn't exist
        """
        if not self.graph.has_node(relation.source_id):
            raise ValueError(f"Source entity {relation.source_id} not found")
        if not self.graph.has_node(relation.target_id):
            raise ValueError(f"Target entity {relation.target_id} not found")

        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            relation_id=relation.id,
            relation_type=relation.type.value,
            verification=relation.verification.model_dump(),
            **relation.model_dump(exclude={'id', 'type', 'source_id', 'target_id', 'verification'})
        )
        self.updated_at = datetime.now()

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve entity data by ID.

        Args:
            entity_id: Entity ID to retrieve

        Returns:
            Entity data dict or None if not found
        """
        if not self.graph.has_node(entity_id):
            return None
        return dict(self.graph.nodes[entity_id])

    def get_relations(self, entity_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """Get all relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "in", "out", or "both"

        Returns:
            List of relation dicts
        """
        relations = []

        if direction in ("out", "both"):
            for target in self.graph.successors(entity_id):
                edge_data = self.graph.edges[entity_id, target]
                relations.append({
                    "source": entity_id,
                    "target": target,
                    **edge_data
                })

        if direction in ("in", "both"):
            for source in self.graph.predecessors(entity_id):
                edge_data = self.graph.edges[source, entity_id]
                relations.append({
                    "source": source,
                    "target": entity_id,
                    **edge_data
                })

        return relations

    def get_metadata(self, factory_version: str) -> GraphMetadata:
        """Generate metadata for export.

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            GraphMetadata object
        """
        from collections import Counter

        # Count entity types
        entity_types = [data.get("entity_type") for _, data in self.graph.nodes(data=True)]
        entity_type_counts = Counter(entity_types)

        # Count documents
        document_count = entity_type_counts.get("DOCUMENT", 0)

        return GraphMetadata(
            case_id=self.case_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            factory_version=factory_version,
            entity_count=self.graph.number_of_nodes(),
            relation_count=self.graph.number_of_edges(),
            document_count=document_count,
            processing_stats={}
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/structure/test_graph.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add tests/structure/test_graph.py farmer_factory/structure/graph.py
git commit -m "feat: add KnowledgeGraph operations

Implement NetworkX-based graph with add/get operations.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: JSON Export Logic

**Files:**
- Create: `farmer_factory/export/exporter.py`
- Create: `tests/export/test_exporter.py`

**Step 1: Create test directory**

```bash
mkdir -p tests/export
touch tests/export/__init__.py
```

**Step 2: Write failing tests for exporter**

Create `tests/export/test_exporter.py`:

```python
"""Tests for graph export logic."""

import pytest
import json
from pathlib import Path
from farmer_factory.export.exporter import GraphExporter
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification,
)


def test_exporter_init():
    """Test GraphExporter initialization."""
    kg = KnowledgeGraph(case_id="case_001")
    exporter = GraphExporter(kg)
    assert exporter.graph == kg


def test_export_to_dict():
    """Test exporting graph to dict."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    relation = Relation(
        id="rel_789",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        )
    )

    kg.add_entity(person)
    kg.add_entity(prop)
    kg.add_relation(relation)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert "metadata" in data
    assert "nodes" in data
    assert "edges" in data
    assert "verification_summary" in data
    assert "entity_type_summary" in data

    assert data["metadata"]["case_id"] == "case_001"
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_export_to_json(tmp_path):
    """Test exporting graph to JSON file."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)

    exporter = GraphExporter(kg)
    output_file = tmp_path / "graph_data.json"
    exporter.export_to_json(output_file, factory_version="1.0.0")

    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    assert data["metadata"]["case_id"] == "case_001"
    assert len(data["nodes"]) == 1


def test_verification_summary():
    """Test verification summary calculation."""
    kg = KnowledgeGraph(case_id="case_001")

    # Add entities with different verification tiers
    for i, tier in enumerate([VerificationTier.TIER_3_AI,
                               VerificationTier.TIER_3_AI,
                               VerificationTier.TIER_2_ANALYST]):
        person = Person(
            id=f"person_{i}",
            entity_type=EntityType.PERSON,
            name=f"Person {i}",
            verification=Verification(tier=tier, confidence=0.85),
            extracted_from="doc_001"
        )
        kg.add_entity(person)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert data["verification_summary"]["TIER_3_AI"] == 2
    assert data["verification_summary"]["TIER_2_ANALYST"] == 1


def test_entity_type_summary():
    """Test entity type summary calculation."""
    kg = KnowledgeGraph(case_id="case_001")

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Person",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001"
    )

    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001"
    )

    kg.add_entity(person)
    kg.add_entity(prop)

    exporter = GraphExporter(kg)
    data = exporter.export_to_dict(factory_version="1.0.0")

    assert data["entity_type_summary"]["PERSON"] == 1
    assert data["entity_type_summary"]["PROPERTY"] == 1
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/export/test_exporter.py -v`

Expected: ImportError (GraphExporter doesn't exist)

**Step 4: Implement GraphExporter**

Create `farmer_factory/export/exporter.py`:

```python
"""
Graph export logic.

Generates graph_data.json and handles Supabase upload.
"""

import json
from pathlib import Path
from typing import Dict, Any
from collections import Counter

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import GraphExport


class GraphExporter:
    """Export knowledge graph to JSON format."""

    def __init__(self, graph: KnowledgeGraph):
        """Initialize exporter.

        Args:
            graph: KnowledgeGraph to export
        """
        self.graph = graph

    def export_to_dict(self, factory_version: str) -> Dict[str, Any]:
        """Export graph to dictionary format.

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            Dictionary matching GraphExport schema
        """
        # Generate metadata
        metadata = self.graph.get_metadata(factory_version)

        # Collect nodes
        nodes = []
        for node_id, node_data in self.graph.graph.nodes(data=True):
            node_dict = {"id": node_id, **node_data}
            nodes.append(node_dict)

        # Collect edges
        edges = []
        for source, target, edge_data in self.graph.graph.edges(data=True):
            edge_dict = {
                "source": source,
                "target": target,
                **edge_data
            }
            edges.append(edge_dict)

        # Calculate verification summary
        verification_summary = self._calculate_verification_summary()

        # Calculate entity type summary
        entity_type_summary = self._calculate_entity_type_summary()

        # Build export dict
        export_data = {
            "metadata": metadata.model_dump(mode='json'),
            "nodes": nodes,
            "edges": edges,
            "verification_summary": verification_summary,
            "entity_type_summary": entity_type_summary,
            "date_range": None  # TODO: Calculate from document dates
        }

        return export_data

    def export_to_json(self, output_path: Path, factory_version: str) -> None:
        """Export graph to JSON file.

        Args:
            output_path: Path to write JSON file
            factory_version: Version string for Farmer Factory
        """
        data = self.export_to_dict(factory_version)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _calculate_verification_summary(self) -> Dict[str, int]:
        """Calculate verification tier counts.

        Returns:
            Dict mapping tier name to count
        """
        tiers = []

        # Count entity verification tiers
        for _, node_data in self.graph.graph.nodes(data=True):
            verification = node_data.get("verification", {})
            tier = verification.get("tier")
            if tier:
                tiers.append(tier)

        # Count relation verification tiers
        for _, _, edge_data in self.graph.graph.edges(data=True):
            verification = edge_data.get("verification", {})
            tier = verification.get("tier")
            if tier:
                tiers.append(tier)

        counts = Counter(tiers)

        # Ensure all tiers are present
        return {
            "TIER_3_AI": counts.get("TIER_3_AI", 0),
            "TIER_2_ANALYST": counts.get("TIER_2_ANALYST", 0),
            "TIER_2_INSTITUTIONAL": counts.get("TIER_2_INSTITUTIONAL", 0),
            "TIER_1_CERTIFIED": counts.get("TIER_1_CERTIFIED", 0),
        }

    def _calculate_entity_type_summary(self) -> Dict[str, int]:
        """Calculate entity type counts.

        Returns:
            Dict mapping entity type to count
        """
        entity_types = []

        for _, node_data in self.graph.graph.nodes(data=True):
            entity_type = node_data.get("entity_type")
            if entity_type:
                entity_types.append(entity_type)

        counts = Counter(entity_types)

        # Ensure all types are present
        return {
            "PERSON": counts.get("PERSON", 0),
            "PROPERTY": counts.get("PROPERTY", 0),
            "ORGANIZATION": counts.get("ORGANIZATION", 0),
            "LOCATION": counts.get("LOCATION", 0),
            "DOCUMENT": counts.get("DOCUMENT", 0),
        }
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/export/test_exporter.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add tests/export/ farmer_factory/export/exporter.py
git commit -m "feat: add GraphExporter for JSON export

Implement graph export to JSON with summaries.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: Update Module Exports

**Files:**
- Modify: `farmer_factory/structure/__init__.py`
- Modify: `farmer_factory/export/__init__.py`

**Step 1: Update structure module exports**

Edit `farmer_factory/structure/__init__.py`:

```python
"""
Graph structure module.
Builds knowledge graph using NetworkX.
Defines entity/relation schemas and graph construction logic.
"""

from .schema import (
    # Enums
    VerificationTier,
    EntityType,
    RelationType,

    # Models
    Verification,
    BaseEntity,
    Person,
    Property,
    Organization,
    Location,
    Document,
    Relation,
    GraphMetadata,
    GraphExport,
)

from .graph import KnowledgeGraph

__all__ = [
    # Enums
    "VerificationTier",
    "EntityType",
    "RelationType",

    # Models
    "Verification",
    "BaseEntity",
    "Person",
    "Property",
    "Organization",
    "Location",
    "Document",
    "Relation",
    "GraphMetadata",
    "GraphExport",

    # Graph
    "KnowledgeGraph",
]
```

**Step 2: Update export module exports**

Edit `farmer_factory/export/__init__.py`:

```python
"""
Export module.
Generates graph_data.json and uploads to Supabase Storage.
Validates schema compliance before export.
"""

from .exporter import GraphExporter

__all__ = ["GraphExporter"]
```

**Step 3: Test imports**

Run: `python -c "from farmer_factory.structure import KnowledgeGraph, Person, Relation; print('Imports successful')"`

Expected: "Imports successful"

**Step 4: Run all tests**

Run: `pytest tests/ -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/__init__.py farmer_factory/export/__init__.py
git commit -m "feat: update module exports

Export all schema models and graph operations.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration test for complete schema workflow."""

import json
from pathlib import Path
from farmer_factory.structure import (
    KnowledgeGraph,
    Person,
    Property,
    Document,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification,
)
from farmer_factory.export import GraphExporter


def test_complete_workflow(tmp_path):
    """Test complete workflow: create graph, add entities/relations, export."""

    # Create graph
    kg = KnowledgeGraph(case_id="case_001")

    # Create document
    doc = Document(
        id="doc_001",
        entity_type=EntityType.DOCUMENT,
        title="Property Transfer Document",
        document_type="contract",
        date="1960-03-26",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        extracted_from="doc_001",
        file_path="/path/to/doc.pdf",
        page_count=3
    )

    # Create person
    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.92
        ),
        extracted_from="doc_001",
        roles=["owner"]
    )

    # Create property
    prop = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        property_type="finca",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        ),
        extracted_from="doc_001",
        area=20.5,
        area_unit="hectares"
    )

    # Add entities
    kg.add_entity(doc)
    kg.add_entity(person)
    kg.add_entity(prop)

    # Create relations
    owns_relation = Relation(
        id="rel_owns",
        type=RelationType.OWNS,
        source_id="person_123",
        target_id="property_456",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85
        ),
        document_id="doc_001"
    )

    mentioned_relation = Relation(
        id="rel_mentioned",
        type=RelationType.MENTIONED_IN,
        source_id="person_123",
        target_id="doc_001",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.95
        )
    )

    # Add relations
    kg.add_relation(owns_relation)
    kg.add_relation(mentioned_relation)

    # Verify graph structure
    assert kg.graph.number_of_nodes() == 3
    assert kg.graph.number_of_edges() == 2

    # Export
    exporter = GraphExporter(kg)
    output_file = tmp_path / "graph_data.json"
    exporter.export_to_json(output_file, factory_version="1.0.0")

    # Verify export
    assert output_file.exists()

    with open(output_file) as f:
        data = json.load(f)

    # Verify structure
    assert data["metadata"]["case_id"] == "case_001"
    assert data["metadata"]["entity_count"] == 3
    assert data["metadata"]["relation_count"] == 2
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2

    # Verify summaries
    assert data["verification_summary"]["TIER_3_AI"] == 5  # 3 entities + 2 relations
    assert data["entity_type_summary"]["PERSON"] == 1
    assert data["entity_type_summary"]["PROPERTY"] == 1
    assert data["entity_type_summary"]["DOCUMENT"] == 1

    # Verify node data
    person_node = next(n for n in data["nodes"] if n["id"] == "person_123")
    assert person_node["name"] == "Mario Ceresa Rodriguez"
    assert person_node["roles"] == ["owner"]

    # Verify edge data
    owns_edge = next(e for e in data["edges"] if e["relation_type"] == "OWNS")
    assert owns_edge["source"] == "person_123"
    assert owns_edge["target"] == "property_456"
    assert owns_edge["document_id"] == "doc_001"
```

**Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`

Expected: Test PASS

**Step 3: Run full test suite**

Run: `pytest tests/ -v --tb=short`

Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for complete workflow

End-to-end test covering graph creation, export, and validation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: Documentation and Final Cleanup

**Files:**
- Create: `farmer_factory/structure/README.md`
- Create: `farmer_factory/export/README.md`

**Step 1: Create structure module README**

Create `farmer_factory/structure/README.md`:

```markdown
# Structure Module

Defines the knowledge graph schema and operations for Civic Table.

## Components

### `schema.py`
Pydantic models for entities, relations, and export format.

**Entity Types:**
- `Person` - Individuals (owners, heirs, witnesses, notaries)
- `Property` - Real estate (fincas, haciendas, urban properties)
- `Organization` - Institutions (banks, courts, government agencies)
- `Location` - Geographic places (cities, provinces, neighborhoods)
- `Document` - Source documents (wills, contracts, certifications)

**Relation Types:**
- Ownership: OWNS, OWNED, INHERITED, SOLD_TO, PURCHASED_FROM
- Family: SPOUSE_OF, CHILD_OF, HEIR_OF
- Boundaries: BORDERS_NORTH/SOUTH/EAST/WEST
- Document: MENTIONED_IN, WITNESSED_BY, NOTARIZED_BY, ISSUED_BY
- Professional: REPRESENTED_BY, EMPLOYED_BY
- Financial: CREDITOR_OF, DEBTOR_OF

**Verification Tiers:**
- `TIER_3_AI` - AI extracted (grey, requires disclaimer)
- `TIER_2_ANALYST` - Civic Table verified (gold)
- `TIER_2_INSTITUTIONAL` - Farmer House verified (gold + FH badge)
- `TIER_1_CERTIFIED` - Legally certified (blue)

### `graph.py`
NetworkX-based knowledge graph operations.

**Usage:**
```python
from farmer_factory.structure import KnowledgeGraph, Person, Relation

# Create graph
kg = KnowledgeGraph(case_id="case_001")

# Add entities
person = Person(
    id="person_123",
    name="Mario Ceresa",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85),
    extracted_from="doc_001"
)
kg.add_entity(person)

# Add relations
relation = Relation(
    id="rel_123",
    type=RelationType.OWNS,
    source_id="person_123",
    target_id="property_456",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.85)
)
kg.add_relation(relation)

# Query
entity_data = kg.get_entity("person_123")
relations = kg.get_relations("person_123", direction="out")
```

## Testing

Run tests:
```bash
pytest tests/structure/ -v
```

## Schema Design

See `docs/plans/2026-01-22-schema-design.md` for complete design rationale.
```

**Step 2: Create export module README**

Create `farmer_factory/export/README.md`:

```markdown
# Export Module

Handles graph export to JSON format and Supabase upload.

## Components

### `exporter.py`
Graph export logic with JSON serialization.

**Usage:**
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

**Export Format:**
```json
{
  "metadata": {
    "case_id": "case_001",
    "entity_count": 45,
    "relation_count": 78,
    "document_count": 12
  },
  "nodes": [...],
  "edges": [...],
  "verification_summary": {...},
  "entity_type_summary": {...}
}
```

## Supabase Upload

TODO: Implement Supabase Storage upload in future task.

## Testing

Run tests:
```bash
pytest tests/export/ -v
```
```

**Step 3: Run final test suite**

Run: `pytest tests/ -v --cov=farmer_factory`

Expected: All tests PASS

**Step 4: Check code quality**

Run: `ruff check farmer_factory/`

Expected: No errors (or fix any that appear)

**Step 5: Commit**

```bash
git add farmer_factory/structure/README.md farmer_factory/export/README.md
git commit -m "docs: add README files for structure and export modules

Document usage and API for schema and export modules.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Completion Checklist

- [x] Verification and EntityType enums
- [x] BaseEntity model
- [x] Person entity
- [x] Property, Organization, Location entities
- [x] Document entity
- [x] RelationType enum and Relation model
- [x] GraphMetadata and GraphExport models
- [x] KnowledgeGraph operations
- [x] GraphExporter with JSON export
- [x] Module exports updated
- [x] Integration test
- [x] Documentation

## Next Steps

After completing this plan:

1. **Implement document intake** (`farmer_factory/intake/`)
2. **Build preprocessing pipeline** (`farmer_factory/prepare/`)
3. **Add OCR integration** (`farmer_factory/extract/ocr.py`)
4. **Implement LLM extraction** (`farmer_factory/extract/llm.py`)
5. **Create CLI commands** (`farmer_factory/cli.py`)

## Notes

- All entity/relation models include verification metadata
- Graph operations validate entity existence before adding relations
- Export includes pre-computed summaries for fast UI loading
- Schema designed for Cuban property documents (1916-1961)
- Flexible date/measurement formats accommodate historical variations
