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
