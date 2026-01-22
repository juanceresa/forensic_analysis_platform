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


def test_extract_from_ocr_text():
    """Test LLM extraction from OCR text (mocked)."""
    from farmer_factory.structure.schema import EntityType

    service = LLMExtractionService()

    # Sample OCR text
    ocr_text = """
    ESCRITURA DE COMPRAVENTA

    En la ciudad de La Habana, a quince de marzo de mil novecientos cincuenta y ocho.

    COMPARECEN:

    De una parte, Don Juan Pérez García, mayor de edad, casado, de nacionalidad cubana,
    vecino de esta ciudad, calle 5ta No. 234, Miramar.

    De otra parte, Doña María López Fernández, mayor de edad, soltera, de nacionalidad cubana,
    vecina de esta ciudad, Avenida 23 No. 567, Vedado.

    MANIFIESTAN:

    Que el Sr. Juan Pérez García es propietario de la finca urbana sita en Miramar,
    calle 5ta No. 234, inscrita en el Registro de la Propiedad bajo el número REG-1958-0042.
    """

    # Extract entities (mocked)
    result = service.extract_from_text(
        text=ocr_text,
        ocr_confidence=0.92,
        document_id="doc_123"
    )

    # Verify result structure
    assert isinstance(result, LLMExtractionResult)
    assert isinstance(result.entities, list)
    assert len(result.entities) > 0  # Should extract at least one entity
    assert isinstance(result.relations, list)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.reasoning, str)
    assert len(result.reasoning) > 0
    assert isinstance(result.metadata, dict)


def test_extract_combines_ocr_confidence():
    """Test that LLM extraction considers OCR confidence."""
    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar, Havana."

    # High OCR confidence
    result_high = service.extract_from_text(ocr_text, 0.95, "doc_123")

    # Low OCR confidence
    result_low = service.extract_from_text(ocr_text, 0.60, "doc_123")

    # Lower OCR confidence should result in lower overall confidence
    assert result_low.confidence < result_high.confidence


def test_extract_entities_have_tier_3_ai():
    """Test that all extracted entities are tagged TIER_3_AI."""
    from farmer_factory.structure.schema import VerificationTier

    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar."
    result = service.extract_from_text(ocr_text, 0.90, "doc_123")

    # All entities should be TIER_3_AI
    for entity in result.entities:
        assert entity.verification.tier == VerificationTier.TIER_3_AI
        assert entity.extracted_from == "doc_123"


def test_extract_includes_reasoning():
    """Test that LLM extraction includes reasoning."""
    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar."
    result = service.extract_from_text(ocr_text, 0.90, "doc_123")

    # Reasoning should be present and non-empty
    assert result.reasoning is not None
    assert len(result.reasoning) > 20  # Should be a substantial explanation
