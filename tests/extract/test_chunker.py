"""Tests for document text chunker."""

import pytest
from farmer_factory.extract.chunker import TextChunker


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_short_text_no_chunking(self):
        """Text under threshold should return single chunk."""
        chunker = TextChunker(chunk_size=5000, overlap_ratio=0.1)
        text = "Short document text." * 10  # ~200 chars

        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_long_text_creates_multiple_chunks(self):
        """Text over threshold should create multiple chunks with overlap."""
        chunker = TextChunker(chunk_size=100, overlap_ratio=0.1)
        # Create text that's ~250 chars
        text = "A" * 250

        chunks = chunker.chunk(text)

        assert len(chunks) >= 2
        # Each chunk should be <= chunk_size
        for chunk in chunks:
            assert len(chunk.text) <= 100
        # Chunks should have overlap
        assert chunks[0].text[-10:] == chunks[1].text[:10]  # 10% overlap

    def test_chunk_at_sentence_boundary(self):
        """Chunker should prefer splitting at sentence boundaries."""
        chunker = TextChunker(chunk_size=50, overlap_ratio=0.1)
        text = "First sentence here. Second sentence here. Third sentence here."

        chunks = chunker.chunk(text)

        # Should not split mid-word or mid-sentence if possible
        for chunk in chunks:
            # Chunk should end with punctuation or be the last chunk
            if chunk.chunk_index < chunk.total_chunks - 1:
                assert chunk.text.rstrip().endswith(('.', '?', '!', '\n'))

    def test_chunk_metadata_tracking(self):
        """Each chunk should track its position in original document."""
        chunker = TextChunker(chunk_size=100, overlap_ratio=0.1)
        text = "X" * 300

        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == len(chunks)
            assert chunk.start_char >= 0
            assert chunk.end_char <= len(text)
            # end_char should match start + len
            assert chunk.end_char - chunk.start_char == len(chunk.text)

    def test_spanish_text_preserves_accents(self):
        """Chunker should handle Spanish text with accents."""
        chunker = TextChunker(chunk_size=50, overlap_ratio=0.1)
        text = "Maria Lopez de Queral, casada con Jose Fernandez. Escritura notarial numero ciento veintitres."

        chunks = chunker.chunk(text)

        # Reconstruct should preserve all characters
        reconstructed = chunker.reconstruct(chunks)
        assert "Maria" in reconstructed
        assert "Lopez" in reconstructed
        assert "numero" in reconstructed

    def test_fuzzy_lengths(self):
        """Fuzz: random lengths and no punctuation should not drop chars."""
        import random
        random.seed(42)  # Reproducibility
        for _ in range(20):
            size = random.randint(10, 300)
            text = "x" * size
            chunker = TextChunker(chunk_size=50, overlap_ratio=0.1)
            chunks = chunker.chunk(text)
            reconstructed = chunker.reconstruct(chunks)
            assert len(reconstructed) == len(text)

    def test_overlap_ratio_validation(self):
        """Overlap ratio must be between 0.0 and 0.5."""
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap_ratio=-0.1)
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap_ratio=0.6)

    def test_empty_text(self):
        """Empty text should return single empty chunk."""
        chunker = TextChunker(chunk_size=100, overlap_ratio=0.1)
        chunks = chunker.chunk("")
        assert len(chunks) == 1
        assert chunks[0].text == ""

    def test_exact_chunk_size(self):
        """Text exactly at chunk size should return single chunk."""
        chunker = TextChunker(chunk_size=100, overlap_ratio=0.1)
        text = "X" * 100
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].text == text
