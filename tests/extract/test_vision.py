"""Unit tests for Vision extraction service."""

import pytest
import numpy as np
from farmer_factory.extract.vision import (
    VisionExtractionService,
    VisionExtractionResult
)
from farmer_factory.structure.schema import Person, Property, Relation


def test_vision_extraction_result_structure():
    """Test VisionExtractionResult dataclass structure."""
    # Create sample entities using actual schema
    from farmer_factory.structure.schema import EntityType, VerificationTier, Verification

    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Test Person",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_123"
    )

    # Create sample relation using actual schema
    from farmer_factory.structure.schema import RelationType

    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.80,
            verified_by=None,
            verified_at=None,
            notes="Document states ownership"
        )
    )

    result = VisionExtractionResult(
        entities=[person],
        relations=[relation],
        confidence=0.85,
        reasoning="Test reasoning",
        metadata={"model": "claude-vision"}
    )

    assert len(result.entities) == 1
    assert len(result.relations) == 1
    assert result.confidence == 0.85
    assert result.reasoning == "Test reasoning"
    assert result.metadata == {"model": "claude-vision"}


def test_vision_service_initialization():
    """Test VisionExtractionService can be initialized."""
    service = VisionExtractionService()
    assert service is not None

    # With API key
    service_with_key = VisionExtractionService(api_key="test_key")
    assert service_with_key is not None


def test_extract_from_handwritten_image():
    """Test vision extraction from handwritten image (mocked)."""
    from farmer_factory.structure.schema import EntityType

    service = VisionExtractionService()

    # Create synthetic handwritten image (grayscale)
    image = np.ones((400, 600), dtype=np.uint8) * 220
    # Simulate irregular handwritten text
    for y in [50, 90, 135, 180, 230]:
        thickness = np.random.randint(2, 5)
        image[y:y+thickness, 60:550] = 70

    # Extract entities (mocked)
    result = service.extract_from_image(image, document_id="doc_123")

    # Verify result structure
    assert isinstance(result, VisionExtractionResult)
    assert isinstance(result.entities, list)
    assert len(result.entities) > 0  # Should extract at least one entity
    assert isinstance(result.relations, list)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.reasoning, str)
    assert len(result.reasoning) > 0
    assert isinstance(result.metadata, dict)


def test_extract_entities_are_valid_pydantic_models():
    """Test that extracted entities are valid Pydantic models."""
    from farmer_factory.structure.schema import EntityType, VerificationTier

    service = VisionExtractionService()

    image = np.ones((400, 600), dtype=np.uint8) * 220
    result = service.extract_from_image(image, document_id="doc_123")

    # All entities should be BaseEntity instances
    for entity in result.entities:
        assert hasattr(entity, 'id')
        assert hasattr(entity, 'entity_type')
        assert hasattr(entity, 'verification')
        assert entity.verification.tier == VerificationTier.TIER_3_AI
        assert entity.extracted_from == "doc_123"


def test_extract_includes_reasoning():
    """Test that vision extraction includes reasoning."""
    service = VisionExtractionService()

    image = np.ones((400, 600), dtype=np.uint8) * 220
    result = service.extract_from_image(image, document_id="doc_123")

    # Reasoning should be present and non-empty
    assert result.reasoning is not None
    assert len(result.reasoning) > 20  # Should be a substantial explanation
    assert "handwritten" in result.reasoning.lower() or "document" in result.reasoning.lower()
