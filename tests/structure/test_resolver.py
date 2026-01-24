"""Tests for dedupe-based entity resolution."""

import pytest
from pathlib import Path
from farmer_factory.structure.resolver import DedupeEntityResolver
from farmer_factory.structure.schema import Person, Location, Property, Organization, Verification, EntityType
from datetime import datetime


def test_resolver_initialization():
    """Test resolver initializes without trained models."""
    resolver = DedupeEntityResolver()
    assert resolver.threshold == 0.5
    assert resolver.dedupers == {}  # No models loaded yet
    assert resolver.model_dir.exists()  # Directory should be created


def test_resolver_custom_threshold():
    """Test resolver accepts custom threshold."""
    resolver = DedupeEntityResolver(threshold=0.7)
    assert resolver.threshold == 0.7


def test_resolver_with_missing_models():
    """Test resolver handles missing models gracefully."""
    resolver = DedupeEntityResolver()

    # Create test entity
    person = Person(
        id="test_1",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Test Person"
    )

    # Should return None when no model exists
    result = resolver.find_similar_entity(person, None)
    assert result is None


def test_entity_data_preparation_person():
    """Test entity data preparation for Person."""
    resolver = DedupeEntityResolver()

    person = Person(
        id="test_1",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Mario Ceresa",
        birth_date="1920",
        residence="Holguin"
    )

    data = resolver._prepare_entity_data(person)

    assert data['name'] == "Mario Ceresa"
    assert data['birth_date'] == "1920"
    assert data['residence'] == "Holguin"
    assert 'profession' in data  # Should have all fields even if None
    assert data['profession'] == ''  # None becomes empty string


def test_entity_data_preparation_location():
    """Test entity data preparation for Location."""
    resolver = DedupeEntityResolver()

    location = Location(
        id="test_1",
        entity_type=EntityType.LOCATION,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Holguin",
        location_type="city",
        country="Cuba"
    )

    data = resolver._prepare_entity_data(location)

    assert data['name'] == "Holguin"
    assert data['location_type'] == "city"
    assert data['country'] == "Cuba"


def test_entity_data_preparation_property():
    """Test entity data preparation for Property."""
    resolver = DedupeEntityResolver()

    property_entity = Property(
        id="test_1",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Finca Aguaras",
        property_type="finca",
        area=50.5
    )

    data = resolver._prepare_entity_data(property_entity)

    assert data['name'] == "Finca Aguaras"
    assert data['property_type'] == "finca"
    assert data['area'] == "50.5"  # Converted to string


def test_entity_data_preparation_organization():
    """Test entity data preparation for Organization."""
    resolver = DedupeEntityResolver()

    org = Organization(
        id="test_1",
        entity_type=EntityType.ORGANIZATION,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Banco de Fomento",
        org_type="bank"
    )

    data = resolver._prepare_entity_data(org)

    assert data['name'] == "Banco de Fomento"
    assert data['org_type'] == "bank"


def test_entity_data_from_dict():
    """Test entity data preparation from graph node data."""
    resolver = DedupeEntityResolver()

    node_data = {
        'name': 'Mario Ceresa',
        'birth_date': '1920',
        'residence': 'Holguin',
        'profession': None,
        'entity_type': 'PERSON'
    }

    data = resolver._prepare_entity_data_from_dict(node_data, 'PERSON')

    assert data['name'] == 'Mario Ceresa'
    assert data['birth_date'] == '1920'
    assert data['residence'] == 'Holguin'
    assert data['profession'] == ''  # None becomes empty string


def test_merge_entities_combines_sources():
    """Test merge entities combines extracted_from sources."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'birth_date': '1920',
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Ceresa",
        birth_date="1920"
    )

    merged = resolver.merge_entities(existing, new_person, match_confidence=0.8)

    # Should combine sources
    assert 'doc_1' in merged['extracted_from']
    assert 'doc_2' in merged['extracted_from']
    assert len(merged['extracted_from']) == 2


def test_merge_entities_high_confidence():
    """Test merge logic with high confidence uses better value."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'birth_date': '1920',
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Cereza Rodriguez",  # Longer, more complete
        birth_date="1922"  # Conflict
    )

    # High confidence match (0.8)
    merged = resolver.merge_entities(existing, new_person, match_confidence=0.8)

    # Should pick better value based on confidence or completeness
    assert 'doc_1' in merged['extracted_from']
    assert 'doc_2' in merged['extracted_from']
    # Birth date should pick higher confidence value (new: 0.9 vs existing: 0.7)
    assert merged['birth_date'] == '1922'


def test_merge_entities_low_confidence():
    """Test merge logic with low confidence creates conflict list."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'birth_date': '1920',
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Cereza",  # Slight variation
        birth_date="1922"  # Conflict
    )

    # Low confidence match (0.6)
    merged = resolver.merge_entities(existing, new_person, match_confidence=0.6)

    # Should create conflict list
    assert isinstance(merged['birth_date'], list)
    assert len(merged['birth_date']) == 2
    assert '1920' in merged['birth_date'][0]
    assert '1922' in merged['birth_date'][1]
    assert 'doc_1' in merged['birth_date'][0]
    assert 'doc_2' in merged['birth_date'][1]


def test_merge_entities_handles_none_values():
    """Test merge entities handles None values correctly."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'birth_date': None,
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Ceresa",
        birth_date="1920"
    )

    merged = resolver.merge_entities(existing, new_person, match_confidence=0.8)

    # Should fill in the None value
    assert merged['birth_date'] == '1920'


def test_merge_entities_handles_list_fields():
    """Test merge entities handles list fields with union."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'alternate_names': ['Mario', 'M. Ceresa'],
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Ceresa",
        alternate_names=['Ceresa', 'M. Ceresa']  # Some overlap
    )

    merged = resolver.merge_entities(existing, new_person, match_confidence=0.8)

    # Should union the lists (no duplicates)
    assert 'Mario' in merged['alternate_names']
    assert 'M. Ceresa' in merged['alternate_names']
    assert 'Ceresa' in merged['alternate_names']
    assert len(merged['alternate_names']) == 3  # No duplicate 'M. Ceresa'


def test_choose_better_value_by_confidence():
    """Test choosing better value based on confidence difference."""
    resolver = DedupeEntityResolver()

    # New value has significantly higher confidence
    result = resolver._choose_better_value("1920", "1922", 0.6, 0.9)
    assert result == "1922"

    # Existing value has significantly higher confidence
    result = resolver._choose_better_value("1920", "1922", 0.9, 0.6)
    assert result == "1920"


def test_choose_better_value_by_completeness():
    """Test choosing better value based on completeness when confidence similar."""
    resolver = DedupeEntityResolver()

    # Similar confidence, new value is longer
    result = resolver._choose_better_value(
        "Mario",
        "Mario Ceresa Rodriguez",
        0.8,
        0.8
    )
    assert result == "Mario Ceresa Rodriguez"

    # Similar confidence, existing value is longer
    result = resolver._choose_better_value(
        "Mario Ceresa Rodriguez",
        "Mario",
        0.8,
        0.8
    )
    assert result == "Mario Ceresa Rodriguez"


def test_create_conflict_list_new():
    """Test creating new conflict list."""
    resolver = DedupeEntityResolver()

    result = resolver._create_conflict_list("1920", "1922", ["doc_1", "doc_2"])

    assert isinstance(result, list)
    assert len(result) == 2
    assert "1920 (doc_1)" == result[0]
    assert "1922 (doc_2)" == result[1]


def test_create_conflict_list_append():
    """Test appending to existing conflict list."""
    resolver = DedupeEntityResolver()

    existing_conflict = ["1920 (doc_1)", "1921 (doc_2)"]
    result = resolver._create_conflict_list(existing_conflict, "1922", ["doc_1", "doc_2", "doc_3"])

    assert isinstance(result, list)
    assert len(result) == 3
    assert "1920 (doc_1)" in result
    assert "1921 (doc_2)" in result
    assert "1922 (doc_3)" in result
