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
