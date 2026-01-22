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
