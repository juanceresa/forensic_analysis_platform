"""Document triage for routing to appropriate processing path."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class DocumentPath(Enum):
    """Processing path for document."""
    TYPED = "typed"
    HANDWRITTEN = "handwritten"


@dataclass
class TriageResult:
    """Result of document triage."""
    path: DocumentPath
    confidence: float  # 0.0-1.0
    reason: str
    metrics: Dict[str, Any]
