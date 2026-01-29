"""Entity deduplication components."""

from .resolver import DedupeEntityResolver
from .config import FIELD_CONFIG
from .train import train_dedupe_model

__all__ = ["DedupeEntityResolver", "FIELD_CONFIG", "train_dedupe_model"]
