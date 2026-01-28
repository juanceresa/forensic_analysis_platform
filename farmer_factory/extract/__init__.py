"""
Extraction module.
Handles OCR (Google Cloud Vision) and LLM-based entity/relation extraction (Anthropic Claude).
All extracted data starts at TIER_3_AI verification level.
"""

from .ocr import OCRService, OCRResult, normalize_ocr_text
from .vision import VisionExtractionService, VisionExtractionResult
from .llm import LLMExtractionService, LLMExtractionResult
from .pipeline import ExtractionPipeline, ExtractionResult
from .validator import SchemaValidator

# Export models for external use
from .models import (
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntityExtractionResult,
    ExtractedRelation,
    RelationExtractionResult
)

# Export API client for direct use if needed
from .api_client import ClaudeAPIClient

# Export prompt builders for customization
from .prompts import (
    build_entity_prompt,
    build_relation_prompt,
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
)

# Export parsers for testing
from .parsers import (
    parse_entity_response,
    parse_relation_response,
    transform_to_final_entities,
    transform_to_final_relations,
)

# Export translator
from .translator import (
    GCPTranslationService,
    translate_text,
    needs_translation,
)

__all__ = [
    # Services
    "OCRService",
    "OCRResult",
    "normalize_ocr_text",
    "VisionExtractionService",
    "VisionExtractionResult",
    "LLMExtractionService",
    "LLMExtractionResult",
    "ExtractionPipeline",
    "ExtractionResult",
    "SchemaValidator",

    # Models
    "PersonExtraction",
    "PropertyExtraction",
    "OrganizationExtraction",
    "LocationExtraction",
    "StructuredEntityExtractionResult",
    "ExtractedRelation",
    "RelationExtractionResult",

    # API Client
    "ClaudeAPIClient",

    # Prompts
    "build_entity_prompt",
    "build_relation_prompt",
    "build_entity_prompt_zero_shot",
    "build_relation_prompt_zero_shot",

    # Parsers
    "parse_entity_response",
    "parse_relation_response",
    "transform_to_final_entities",
    "transform_to_final_relations",

    # Translator
    "GCPTranslationService",
    "translate_text",
    "needs_translation",
]
