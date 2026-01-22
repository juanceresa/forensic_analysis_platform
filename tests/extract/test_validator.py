"""Unit tests for Schema Validator."""

import pytest
from pydantic import ValidationError
from farmer_factory.extract.validator import SchemaValidator
from farmer_factory.structure.schema import (
    Person, Property, EntityType, VerificationTier, Verification,
    Relation, RelationType
)


def test_validate_entity_valid_person():
    """Test validating a valid Person entity dict."""
    validator = SchemaValidator()

    person_dict = {
        "id": "p1",
        "entity_type": "PERSON",
        "name": "Juan Pérez",
        "alternate_names": [],
        "roles": ["owner"],
        "verification": {
            "tier": "TIER_3_AI",
            "confidence": 0.85,
            "verified_by": None,
            "verified_at": None,
            "notes": None
        },
        "extracted_from": "doc_123"
    }

    result = validator.validate_entity(person_dict, EntityType.PERSON)

    assert isinstance(result, Person)
    assert result.id == "p1"
    assert result.name == "Juan Pérez"
    assert result.verification.tier == VerificationTier.TIER_3_AI


def test_validate_entity_invalid_data():
    """Test validating invalid entity data raises ValidationError."""
    validator = SchemaValidator()

    # Missing required field
    person_dict = {
        "id": "p1",
        "entity_type": "PERSON",
        # Missing 'name' field
        "verification": {
            "tier": "TIER_3_AI",
            "confidence": 0.85
        },
        "extracted_from": "doc_123"
    }

    with pytest.raises(ValidationError):
        validator.validate_entity(person_dict, EntityType.PERSON)


def test_validate_extraction_all_valid():
    """Test validating a batch of all valid entities."""
    validator = SchemaValidator()

    entities = [
        {
            "id": "p1",
            "entity_type": "PERSON",
            "name": "Juan Pérez",
            "alternate_names": [],
            "roles": [],
            "verification": {
                "tier": "TIER_3_AI",
                "confidence": 0.85,
                "verified_by": None,
                "verified_at": None,
                "notes": None
            },
            "extracted_from": "doc_123"
        }
    ]

    relations = [
        {
            "id": "r1",
            "type": "OWNS",
            "source_id": "p1",
            "target_id": "prop1",
            "verification": {
                "tier": "TIER_3_AI",
                "confidence": 0.80,
                "verified_by": None,
                "verified_at": None,
                "notes": None
            }
        }
    ]

    valid_entities, valid_relations = validator.validate_extraction(entities, relations)

    assert len(valid_entities) == 1
    assert len(valid_relations) == 1
    assert isinstance(valid_entities[0], Person)
    assert isinstance(valid_relations[0], Relation)


def test_validate_extraction_partial_valid():
    """Test validating a batch with some invalid entities."""
    validator = SchemaValidator()

    entities = [
        # Valid entity
        {
            "id": "p1",
            "entity_type": "PERSON",
            "name": "Juan Pérez",
            "alternate_names": [],
            "roles": [],
            "verification": {
                "tier": "TIER_3_AI",
                "confidence": 0.85,
                "verified_by": None,
                "verified_at": None,
                "notes": None
            },
            "extracted_from": "doc_123"
        },
        # Invalid entity (missing name)
        {
            "id": "p2",
            "entity_type": "PERSON",
            "alternate_names": [],
            "roles": [],
            "verification": {
                "tier": "TIER_3_AI",
                "confidence": 0.85,
                "verified_by": None,
                "verified_at": None,
                "notes": None
            },
            "extracted_from": "doc_123"
        }
    ]

    relations = []

    valid_entities, valid_relations = validator.validate_extraction(entities, relations)

    # Should only return valid entities
    assert len(valid_entities) == 1
    assert valid_entities[0].id == "p1"


def test_validate_extraction_logs_errors(caplog):
    """Test that validation errors are logged."""
    validator = SchemaValidator()

    entities = [
        {
            "id": "p1",
            "entity_type": "PERSON",
            # Missing required 'name' field
            "verification": {
                "tier": "TIER_3_AI",
                "confidence": 0.85
            },
            "extracted_from": "doc_123"
        }
    ]

    relations = []

    validator.validate_extraction(entities, relations)

    # Should have logged validation error
    assert "Validation error" in caplog.text or "validation" in caplog.text.lower()
