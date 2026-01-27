"""Document text chunker for LLM extraction.

Implements optimal chunking strategy from Chilean dictatorship KG paper:
- 5000 character chunks with 10% overlap
- Prefers sentence boundaries for splits
- Tracks chunk positions for provenance
"""

from dataclasses import dataclass
from typing import List
import re


@dataclass
class TextChunk:
    """A chunk of text with position metadata."""

    text: str
    start_char: int
    end_char: int
    chunk_index: int
    total_chunks: int


class TextChunker:
    """
    Splits long documents into overlapping chunks for LLM processing.

    Based on optimal parameters from Chilean KG paper (arXiv:2408.11975):
    - Default chunk size: 5000 characters
    - Default overlap: 10% (500 characters)
    - Splits at sentence boundaries when possible
    - Chunks never exceed chunk_size; overlap handled via start offset
    """

    # Sentence-ending patterns (Spanish and English)
    SENTENCE_END_PATTERN = re.compile(r"[.!?]\s+|\n\n|\n(?=[A-Z])")

    def __init__(self, chunk_size: int = 5000, overlap_ratio: float = 0.1):
        """
        Initialize chunker.

        Args:
            chunk_size: Target size for each chunk in characters
            overlap_ratio: Fraction of chunk_size to overlap (0.0-0.5)
        """
        if not 0.0 <= overlap_ratio <= 0.5:
            raise ValueError("overlap_ratio must be between 0.0 and 0.5")

        self.chunk_size = chunk_size
        self.overlap_size = int(chunk_size * overlap_ratio)

    def chunk(self, text: str) -> List[TextChunk]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full document text

        Returns:
            List of TextChunk objects with position metadata
        """
        if len(text) <= self.chunk_size:
            # Short text - single chunk
            return [
                TextChunk(
                    text=text,
                    start_char=0,
                    end_char=len(text),
                    chunk_index=0,
                    total_chunks=1,
                )
            ]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Calculate chunk end position
            chunk_end = min(current_pos + self.chunk_size, len(text))

            # If not at end of text, try to find a sentence boundary
            if chunk_end < len(text):
                chunk_end = self._find_sentence_boundary(text, current_pos, chunk_end)

            # Extract chunk text
            chunk_text = text[current_pos:chunk_end]

            chunks.append(
                TextChunk(
                    text=chunk_text,
                    start_char=current_pos,
                    end_char=chunk_end,
                    chunk_index=len(chunks),
                    total_chunks=0,  # Will update after
                )
            )

            # Move position, accounting for overlap
            if chunk_end >= len(text):
                break
            current_pos = max(chunk_end - self.overlap_size, current_pos + 1)

        # Update total_chunks in all chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _find_sentence_boundary(self, text: str, start: int, target_end: int) -> int:
        """
        Find the best sentence boundary near target_end.

        Searches backward from target_end to find sentence-ending punctuation.
        If no boundary found within 20% of chunk_size, uses target_end.
        """
        # Search window: from 80% to 100% of chunk_size
        search_start = max(start, target_end - int(self.chunk_size * 0.2))
        search_text = text[search_start:target_end]

        # Find all sentence boundaries in search window
        matches = list(self.SENTENCE_END_PATTERN.finditer(search_text))

        if matches:
            # Use the last boundary found (closest to target)
            last_match = matches[-1]
            return search_start + last_match.end()

        # No sentence boundary found - fall back to word boundary
        # Look for last whitespace
        last_space = search_text.rfind(" ")
        if last_space > 0:
            return search_start + last_space + 1

        # No good boundary - use target
        return target_end

    def reconstruct(self, chunks: List[TextChunk]) -> str:
        """
        Reconstruct original text from chunks (for validation).

        Note: Due to overlap, this removes duplicate overlap regions.
        """
        if not chunks:
            return ""

        if len(chunks) == 1:
            return chunks[0].text

        # Sort by chunk_index
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)

        # Start with first chunk
        result = sorted_chunks[0].text

        # Append non-overlapping parts of subsequent chunks
        for i in range(1, len(sorted_chunks)):
            chunk = sorted_chunks[i]
            # Skip the overlap portion
            non_overlap_start = min(self.overlap_size, len(chunk.text))
            if non_overlap_start < len(chunk.text):
                result += chunk.text[non_overlap_start:]

        return result
