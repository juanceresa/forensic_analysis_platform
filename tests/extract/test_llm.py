"""Unit tests for LLM extraction service."""

import pytest
from farmer_factory.extract.llm import (
    LLMExtractionService,
    LLMExtractionResult
)
from farmer_factory.structure.schema import Person, Property, Relation


def test_llm_extraction_result_structure():
    """Test LLMExtractionResult dataclass structure."""
    from farmer_factory.structure.schema import (
        EntityType, VerificationTier, Verification, RelationType
    )

    # Create sample entities
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

    # Create sample relation
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

    result = LLMExtractionResult(
        entities=[person],
        relations=[relation],
        confidence=0.85,
        reasoning="Test reasoning",
        metadata={"model": "claude-3"}
    )

    assert len(result.entities) == 1
    assert len(result.relations) == 1
    assert result.confidence == 0.85
    assert result.reasoning == "Test reasoning"
    assert result.metadata == {"model": "claude-3"}


def test_llm_service_initialization():
    """Test LLMExtractionService can be initialized."""
    service = LLMExtractionService()
    assert service is not None

    # With API key
    service_with_key = LLMExtractionService(api_key="test_key")
    assert service_with_key is not None
