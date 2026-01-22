"""LLM extraction service for entity extraction from OCR text using Claude API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from farmer_factory.structure.schema import BaseEntity, Relation


@dataclass
class LLMExtractionResult:
    """Result from LLM-based entity extraction."""
    entities: List[BaseEntity]   # Extracted entities
    relations: List[Relation]    # Extracted relations
    confidence: float            # Extraction confidence
    reasoning: str               # Extraction reasoning
    metadata: Dict[str, Any]


class LLMExtractionService:
    """Wrapper for Claude text API for entity extraction from OCR text (mocked for testing)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key
