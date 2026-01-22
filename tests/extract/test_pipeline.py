"""Unit tests for Extraction Pipeline."""

import pytest
import numpy as np
from farmer_factory.prepare import DocumentPath, ProcessedPage
from farmer_factory.extract.pipeline import ExtractionPipeline, ExtractionResult
from farmer_factory.extract.ocr import OCRService, OCRResult
from farmer_factory.extract.vision import VisionExtractionService
from farmer_factory.extract.llm import LLMExtractionService
from farmer_factory.extract.validator import SchemaValidator
from farmer_factory.structure.schema import (
    Person, EntityType, VerificationTier, Verification
)


def test_extraction_result_structure():
    """Test ExtractionResult dataclass structure."""
    # Create sample entity
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

    # Create OCR result
    ocr_result = OCRResult(
        text="Sample text",
        confidence=0.90,
        page_confidence=0.88,
        blocks=[],
        metadata={}
    )

    result = ExtractionResult(
        entities=[person],
        relations=[],
        ocr_result=ocr_result,
        confidence_scores={"overall": 0.85, "ocr": 0.90},
        path=DocumentPath.TYPED,
        processing_metadata={"duration_ms": 500}
    )

    assert len(result.entities) == 1
    assert len(result.relations) == 0
    assert result.ocr_result == ocr_result
    assert result.confidence_scores["overall"] == 0.85
    assert result.path == DocumentPath.TYPED
    assert result.processing_metadata["duration_ms"] == 500


def test_extraction_pipeline_initialization():
    """Test ExtractionPipeline can be initialized with services."""
    ocr_service = OCRService()
    vision_service = VisionExtractionService()
    llm_service = LLMExtractionService()
    validator = SchemaValidator()

    pipeline = ExtractionPipeline(
        ocr_service=ocr_service,
        vision_service=vision_service,
        llm_service=llm_service,
        validator=validator
    )

    assert pipeline is not None
    assert pipeline.ocr_service == ocr_service
    assert pipeline.vision_service == vision_service
    assert pipeline.llm_service == llm_service
    assert pipeline.validator == validator


def test_extract_page_typed_path():
    """Test extracting from a TYPED document (OCR + LLM path)."""
    # Initialize services
    ocr_service = OCRService()
    vision_service = VisionExtractionService()
    llm_service = LLMExtractionService()
    validator = SchemaValidator()

    pipeline = ExtractionPipeline(
        ocr_service=ocr_service,
        vision_service=vision_service,
        llm_service=llm_service,
        validator=validator
    )

    # Create preprocessed TYPED page
    binary_image = np.ones((400, 600), dtype=np.uint8) * 255
    binary_image[50:70, 100:500] = 0  # Simulate text

    processed_page = ProcessedPage(
        image=binary_image,
        path=DocumentPath.TYPED,
        metadata={"skew_angle": 0.5, "triage_confidence": 0.9}
    )

    # Extract entities
    result = pipeline.extract_page(processed_page, document_id="doc_123")

    # Verify result
    assert isinstance(result, ExtractionResult)
    assert result.path == DocumentPath.TYPED
    assert result.ocr_result is not None  # TYPED path has OCR
    assert len(result.entities) > 0
    assert isinstance(result.confidence_scores, dict)
    assert "ocr_confidence" in result.confidence_scores
    assert "llm_confidence" in result.confidence_scores
    assert "combined_confidence" in result.confidence_scores


def test_extract_page_handwritten_path():
    """Test extracting from a HANDWRITTEN document (Vision path)."""
    # Initialize services
    ocr_service = OCRService()
    vision_service = VisionExtractionService()
    llm_service = LLMExtractionService()
    validator = SchemaValidator()

    pipeline = ExtractionPipeline(
        ocr_service=ocr_service,
        vision_service=vision_service,
        llm_service=llm_service,
        validator=validator
    )

    # Create preprocessed HANDWRITTEN page
    grayscale_image = np.ones((400, 600), dtype=np.uint8) * 220
    for y in [50, 90, 135]:
        grayscale_image[y:y+3, 60:550] = 70  # Simulate handwriting

    processed_page = ProcessedPage(
        image=grayscale_image,
        path=DocumentPath.HANDWRITTEN,
        metadata={"skew_angle": 1.2, "triage_confidence": 0.85}
    )

    # Extract entities
    result = pipeline.extract_page(processed_page, document_id="doc_456")

    # Verify result
    assert isinstance(result, ExtractionResult)
    assert result.path == DocumentPath.HANDWRITTEN
    assert result.ocr_result is None  # HANDWRITTEN path skips OCR
    assert len(result.entities) > 0
    assert isinstance(result.confidence_scores, dict)
    assert "vision_confidence" in result.confidence_scores


def test_extract_page_tags_tier_3_ai():
    """Test that all extracted entities are tagged TIER_3_AI."""
    pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    # Create test page
    image = np.ones((400, 600), dtype=np.uint8) * 255
    processed_page = ProcessedPage(
        image=image,
        path=DocumentPath.TYPED,
        metadata={}
    )

    result = pipeline.extract_page(processed_page, document_id="doc_789")

    # All entities should be TIER_3_AI
    for entity in result.entities:
        assert entity.verification.tier == VerificationTier.TIER_3_AI
