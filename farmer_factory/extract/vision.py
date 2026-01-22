"""Vision extraction service for handwritten documents using Claude Vision API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from farmer_factory.structure.schema import BaseEntity, Relation


@dataclass
class VisionExtractionResult:
    """Result from vision-based entity extraction."""
    entities: List[BaseEntity]   # Extracted entities (Pydantic models)
    relations: List[Relation]    # Extracted relations
    confidence: float            # Overall extraction confidence
    reasoning: str               # Claude's reasoning for extractions
    metadata: Dict[str, Any]     # Vision model metadata


class VisionExtractionService:
    """Wrapper for Claude Vision API for handwritten document extraction (mocked for testing)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Vision extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key
