"""Extraction pipeline orchestrating OCR, Vision, and LLM services."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from farmer_factory.prepare import DocumentPath, ProcessedPage
from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.ocr import OCRService, OCRResult
from farmer_factory.extract.vision import VisionExtractionService
from farmer_factory.extract.llm import LLMExtractionService
from farmer_factory.extract.validator import SchemaValidator


@dataclass
class ExtractionResult:
    """Complete extraction result for a document page."""
    entities: List[BaseEntity]              # All extracted entities
    relations: List[Relation]               # All extracted relations
    ocr_result: Optional[OCRResult]         # OCR output (TYPED path only)
    confidence_scores: Dict[str, float]     # Multi-level confidence tracking
    path: DocumentPath                      # Which path was used
    processing_metadata: Dict[str, Any]     # Processing metadata
    extraction_flags: List[str] = field(default_factory=list)  # Flags for incomplete/failed extractions


class ExtractionPipeline:
    """Orchestrates the two-path extraction process."""

    def __init__(
        self,
        ocr_service: OCRService,
        vision_service: VisionExtractionService,
        llm_service: LLMExtractionService,
        validator: SchemaValidator
    ):
        """
        Initialize extraction pipeline with services.

        Args:
            ocr_service: OCR service for typed documents
            vision_service: Vision service for handwritten documents
            llm_service: LLM service for entity extraction from text
            validator: Schema validator for Pydantic models
        """
        self.ocr_service = ocr_service
        self.vision_service = vision_service
        self.llm_service = llm_service
        self.validator = validator

    def extract_page(
        self,
        processed_page: ProcessedPage,
        document_id: str
    ) -> ExtractionResult:
        """
        Extract entities from preprocessed page.

        Routes to appropriate extraction path based on document type.

        Args:
            processed_page: Preprocessed page from prepare module
            document_id: Document identifier for entity tracking

        Returns:
            ExtractionResult with entities, relations, and confidence scores
        """
        if processed_page.path == DocumentPath.TYPED:
            return self._extract_typed_path(processed_page, document_id)
        elif processed_page.path == DocumentPath.HANDWRITTEN:
            return self._extract_handwritten_path(processed_page, document_id)
        else:
            raise ValueError(f"Unknown document path: {processed_page.path}")

    def _extract_typed_path(
        self,
        processed_page: ProcessedPage,
        document_id: str
    ) -> ExtractionResult:
        """
        Extract from TYPED document: OCR → LLM → Validate.

        Args:
            processed_page: Preprocessed binary image
            document_id: Document identifier

        Returns:
            ExtractionResult with OCR + LLM extraction
        """
        # Step 1: OCR extraction
        ocr_result = self.ocr_service.extract_text(processed_page.image)

        # Step 2: LLM entity extraction from OCR text
        llm_result = self.llm_service.extract_from_text(
            text=ocr_result.text,
            ocr_confidence=ocr_result.confidence,
            document_id=document_id
        )

        # Step 3: Validate entities and relations
        # (LLM already returns Pydantic models, but validator ensures consistency)
        entity_dicts = [e.model_dump(mode="json") for e in llm_result.entities]
        relation_dicts = [r.model_dump(mode="json") for r in llm_result.relations]
        validated_entities, validated_relations = self.validator.validate_extraction(
            entities=entity_dicts,
            relations=relation_dicts
        )

        # Calculate combined confidence: min of OCR and LLM
        combined_confidence = min(ocr_result.confidence, llm_result.confidence)

        # Build confidence scores
        confidence_scores = {
            "ocr_confidence": ocr_result.confidence,
            "llm_confidence": llm_result.confidence,
            "combined_confidence": combined_confidence
        }

        # Check for relation extraction failure
        relation_status = llm_result.metadata.get("relation_extraction_status", "UNKNOWN")
        if relation_status == "FAILED":
            extraction_flags = ["RELATION_EXTRACTION_FAILED"]
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"⚠️  {document_id} INCOMPLETE - has entities but relation extraction failed"
            )
        else:
            extraction_flags = []

        # Processing metadata
        processing_metadata = {
            "path": "TYPED",
            "ocr_metadata": ocr_result.metadata,
            "llm_metadata": llm_result.metadata,
            "preprocessing_metadata": processed_page.metadata,
            "relation_count": len(validated_relations),
            "relation_extraction_status": relation_status
        }

        return ExtractionResult(
            entities=validated_entities,
            relations=validated_relations,
            ocr_result=ocr_result,
            confidence_scores=confidence_scores,
            path=DocumentPath.TYPED,
            processing_metadata=processing_metadata,
            extraction_flags=extraction_flags
        )

    def _extract_handwritten_path(
        self,
        processed_page: ProcessedPage,
        document_id: str
    ) -> ExtractionResult:
        """
        Extract from HANDWRITTEN document: Vision → Validate.

        Args:
            processed_page: Preprocessed grayscale image
            document_id: Document identifier

        Returns:
            ExtractionResult with Vision extraction
        """
        # Step 1: Vision entity extraction directly from image
        vision_result = self.vision_service.extract_from_image(
            image=processed_page.image,
            document_id=document_id
        )

        # Step 2: Validate entities and relations
        # (Vision already returns Pydantic models, but validator ensures consistency)
        entity_dicts = [e.model_dump(mode="json") for e in vision_result.entities]
        relation_dicts = [r.model_dump(mode="json") for r in vision_result.relations]
        validated_entities, validated_relations = self.validator.validate_extraction(
            entities=entity_dicts,
            relations=relation_dicts
        )

        # Build confidence scores
        confidence_scores = {
            "vision_confidence": vision_result.confidence
        }

        # Processing metadata
        processing_metadata = {
            "path": "HANDWRITTEN",
            "vision_metadata": vision_result.metadata,
            "preprocessing_metadata": processed_page.metadata
        }

        return ExtractionResult(
            entities=validated_entities,
            relations=validated_relations,
            ocr_result=None,  # No OCR in handwritten path
            confidence_scores=confidence_scores,
            path=DocumentPath.HANDWRITTEN,
            processing_metadata=processing_metadata
        )
