"""Integration tests for full extraction pipeline."""

import pytest
import numpy as np
from farmer_factory.prepare import PreprocessingPipeline, DocumentPath
from farmer_factory.extract import (
    ExtractionPipeline,
    OCRService,
    VisionExtractionService,
    LLMExtractionService,
    SchemaValidator,
)
from farmer_factory.structure.schema import VerificationTier


def test_full_pipeline_typed_document():
    """Test full pipeline: preprocessing → extraction for TYPED document."""
    # Create realistic typed document image
    image = np.ones((400, 600), dtype=np.uint8) * 235

    # Add regular typed text lines
    for y in range(40, 360, 25):
        # Simulate text blocks
        image[y:y+12, 50:550] = np.random.randint(40, 80, (12, 500))

    # Preprocess through prepare pipeline
    prep_pipeline = PreprocessingPipeline()
    processed_page = prep_pipeline.process_page(image)

    # Extract entities through extract pipeline
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    result = extract_pipeline.extract_page(processed_page, document_id="test_doc_001")

    # Verify path routing
    assert result.path == DocumentPath.TYPED

    # Verify OCR was used
    assert result.ocr_result is not None
    assert result.ocr_result.text is not None
    assert len(result.ocr_result.text) > 0

    # Verify entities extracted
    assert len(result.entities) > 0

    # Verify all entities are TIER_3_AI
    for entity in result.entities:
        assert entity.verification.tier == VerificationTier.TIER_3_AI
        assert entity.extracted_from == "test_doc_001"

    # Verify confidence tracking
    assert "ocr_confidence" in result.confidence_scores
    assert "llm_confidence" in result.confidence_scores
    assert "combined_confidence" in result.confidence_scores

    # Combined confidence should be min of OCR and LLM
    assert result.confidence_scores["combined_confidence"] == min(
        result.confidence_scores["ocr_confidence"],
        result.confidence_scores["llm_confidence"]
    )


def test_full_pipeline_handwritten_document():
    """Test full pipeline: preprocessing → extraction for HANDWRITTEN document."""
    # Create realistic handwritten document
    image = np.ones((400, 600), dtype=np.uint8) * 220

    # Add irregular handwritten lines
    y_positions = [40, 70, 105, 135, 170, 210, 245, 280, 320, 360]
    for y in y_positions:
        thickness = np.random.randint(3, 8)
        start_x = np.random.randint(40, 60)
        end_x = np.random.randint(530, 580)
        intensity = np.random.randint(30, 90)
        image[y:y+thickness, start_x:end_x] = intensity

    # Preprocess through prepare pipeline
    prep_pipeline = PreprocessingPipeline()
    processed_page = prep_pipeline.process_page(image)

    # Extract entities through extract pipeline
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    result = extract_pipeline.extract_page(processed_page, document_id="test_doc_002")

    # Verify path routing
    assert result.path == DocumentPath.HANDWRITTEN

    # Verify OCR was NOT used
    assert result.ocr_result is None

    # Verify entities extracted via vision
    assert len(result.entities) > 0

    # Verify all entities are TIER_3_AI
    for entity in result.entities:
        assert entity.verification.tier == VerificationTier.TIER_3_AI
        assert entity.extracted_from == "test_doc_002"

    # Verify confidence tracking
    assert "vision_confidence" in result.confidence_scores


def test_integration_preserves_preprocessing_metadata():
    """Test that extraction result includes preprocessing metadata."""
    image = np.ones((400, 600), dtype=np.uint8) * 235

    # Preprocess
    prep_pipeline = PreprocessingPipeline()
    processed_page = prep_pipeline.process_page(image)

    # Extract
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )
    result = extract_pipeline.extract_page(processed_page, document_id="test_doc_003")

    # Should include preprocessing metadata
    assert "preprocessing_metadata" in result.processing_metadata
    assert "skew_angle" in result.processing_metadata["preprocessing_metadata"]
    assert "triage_confidence" in result.processing_metadata["preprocessing_metadata"]
