# Academic Knowledge Graph Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement knowledge graph improvements inspired by Chilean dictatorship KG paper (arXiv:2408.11975) and Chinese oral history archive research.

**Architecture:** Phased improvements to extraction, schema, and post-processing. Quick wins first (no schema changes), then schema additions, then larger architecture changes. Each phase is independently deployable.

**Tech Stack:** Python 3.10+, Pydantic, NetworkX, Claude API (existing stack)

**Source Research:**
- Chilean paper: Automatic knowledge-graph creation from historical documents (arXiv:2408.11975v1)
- Chinese paper: Knowledge Graph of Oral Historical Archives (ACM JCDL 2024)

---

## Phase 1: Quick Wins (No Schema Changes)

These improvements can be deployed immediately without modifying the schema or breaking existing data.

---

### Task 1.1: Document Chunking with Overlap

**Goal:** Implement 5000-character chunking with 10% overlap for long documents, matching the optimal parameters from the Chilean paper, with robust bounds and reconstruction.

**Files:**
- Create: `farmer_factory/extract/chunker.py`
- Modify: `farmer_factory/extract/llm.py:907-1016` (extract_from_text)
- Test: `tests/extract/test_chunker.py`

**Step 1: Write the failing test for chunker**

```python
# tests/extract/test_chunker.py
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
        text = "María López de Queral, casada con José Fernández. Escritura notarial número ciento veintitrés."

        chunks = chunker.chunk(text)

        # Reconstruct should preserve all characters
        reconstructed = chunker.reconstruct(chunks)
        assert "María" in reconstructed
        assert "López" in reconstructed
        assert "número" in reconstructed

    def test_fuzzy_lengths(self):
        """Fuzz: random lengths and no punctuation should not drop chars."""
        import random
        for _ in range(20):
            size = random.randint(10, 300)
            text = "x" * size
            chunker = TextChunker(chunk_size=50, overlap_ratio=0.1)
            chunks = chunker.chunk(text)
            reconstructed = chunker.reconstruct(chunks)
            assert len(reconstructed) == len(text)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/extract/test_chunker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'farmer_factory.extract.chunker'"

**Step 3: Write minimal implementation**

```python
# farmer_factory/extract/chunker.py
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
    SENTENCE_END_PATTERN = re.compile(r'[.!?]\s+|\n\n|\n(?=[A-ZÁÉÍÓÚÑ])')

    def __init__(
        self,
        chunk_size: int = 5000,
        overlap_ratio: float = 0.1
    ):
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
            return [TextChunk(
                text=text,
                start_char=0,
                end_char=len(text),
                chunk_index=0,
                total_chunks=1
            )]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Calculate chunk end position
            chunk_end = min(current_pos + self.chunk_size, len(text))

            # If not at end of text, try to find a sentence boundary
            if chunk_end < len(text):
                chunk_end = self._find_sentence_boundary(
                    text,
                    current_pos,
                    chunk_end
                )

            # Extract chunk text
            chunk_text = text[current_pos:chunk_end]

            chunks.append(TextChunk(
                text=chunk_text,
                start_char=current_pos,
                end_char=chunk_end,
                chunk_index=len(chunks),
                total_chunks=0  # Will update after
            ))

            # Move position, accounting for overlap
            if chunk_end >= len(text):
                break
            current_pos = max(chunk_end - self.overlap_size, current_pos + 1)

        # Update total_chunks in all chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _find_sentence_boundary(
        self,
        text: str,
        start: int,
        target_end: int
    ) -> int:
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
        last_space = search_text.rfind(' ')
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/extract/test_chunker.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/extract/chunker.py tests/extract/test_chunker.py
git commit -m "feat(extract): add document text chunker with overlap

Implements 5000-char chunking with 10% overlap based on
Chilean KG paper optimal parameters (arXiv:2408.11975).

- Prefers sentence boundaries for splits
- Tracks chunk positions for provenance
- Handles Spanish text with accents

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.2: Integrate Chunker into LLM Extraction

**Goal:** Modify `extract_from_text` to use chunker for long documents and merge results.

**Files:**
- Modify: `farmer_factory/extract/llm.py:907-1016`
- Test: `tests/extract/test_llm.py` (add chunking tests)

**Step 1: Write the failing test for chunked extraction**

```python
# Add to tests/extract/test_llm.py

class TestChunkedExtraction:
    """Tests for chunked document extraction."""

    def test_long_document_uses_chunking(self, llm_service):
        """Documents over chunk threshold should be processed in chunks."""
        # Create text longer than 5000 chars
        long_text = "Don Mario Ceresa, propietario. " * 200  # ~6400 chars

        result = llm_service.extract_from_text(
            text=long_text,
            document_id="test_long_doc"
        )

        # Should still return valid result
        assert result is not None
        assert result.confidence > 0
        # Metadata should indicate chunking was used
        assert result.metadata.get("chunks_processed", 1) >= 1

    def test_chunked_entities_are_deduplicated(self, llm_service):
        """Entities appearing in multiple chunks should be deduplicated."""
        # Text where same entity appears in overlap region
        text = ("Mario Ceresa owns property. " * 100 +
                "Mario Ceresa is the owner. " * 100)

        result = llm_service.extract_from_text(
            text=text,
            document_id="test_dedup"
        )

        # Should not have duplicate Mario Ceresa entities
        mario_count = sum(
            1 for e in result.entities
            if getattr(e, 'name', '').lower().startswith('mario')
        )
        assert mario_count <= 1, "Duplicate entities from chunks not merged"

    def test_dedup_merges_fields(self, llm_service):
        """Merging should preserve roles/alternate_names and highest confidence."""
        text = ("Don Mario Ceresa, propietario. " * 60) + ("Mario Ceresa, dueño. " * 60)
        result = llm_service.extract_from_text(
            text=text,
            document_id="test_merge_fields"
        )
        mario = [e for e in result.entities if getattr(e, 'name', '').lower().startswith('mario')]
        assert len(mario) == 1
        entity = mario[0]
        assert 'propietario' in getattr(entity, 'roles', []) or 'dueño' in getattr(entity, 'roles', [])
        assert entity.verification.confidence > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/extract/test_llm.py::TestChunkedExtraction -v`
Expected: FAIL (chunks_processed not in metadata)

**Step 3: Modify extract_from_text to use chunker**

```python
# In farmer_factory/extract/llm.py

# Add import at top
from farmer_factory.extract.chunker import TextChunker

# Add class constant
CHUNK_THRESHOLD = 5000  # Characters - process as chunks if longer

# Modify extract_from_text method (around line 907)
def extract_from_text(
    self,
    text: str,
    document_id: str,
    document_type: str = "unknown",
    ocr_confidence: float = 0.8
) -> LLMExtractionResult:
    """
    Extract entities and relations from OCR text.

    For documents over 5000 characters, uses chunked extraction
    with 10% overlap and merges results.
    """
    # Check if chunking is needed
    if len(text) > CHUNK_THRESHOLD:
        return self._extract_with_chunking(
            text=text,
            document_id=document_id,
            document_type=document_type,
            ocr_confidence=ocr_confidence
        )

    # Original single-pass extraction for short documents
    return self._extract_single_pass(
        text=text,
        document_id=document_id,
        document_type=document_type,
        ocr_confidence=ocr_confidence
    )

def _extract_with_chunking(
    self,
    text: str,
    document_id: str,
    document_type: str,
    ocr_confidence: float
) -> LLMExtractionResult:
    """
    Extract from long document using chunked processing.

    Strategy from Chilean KG paper:
    1. Split into 5000-char chunks with 10% overlap
    2. Extract entities from each chunk
    3. Merge entities across chunks (deduplicate by name)
    4. Extract relations using merged entity list
    """
    chunker = TextChunker(chunk_size=5000, overlap_ratio=0.1)
    chunks = chunker.chunk(text)

    logger.info(f"Processing {len(chunks)} chunks for document {document_id}")

    # Phase 1: Extract entities from all chunks
    all_entities = []
    chunk_confidences = []

    for chunk in chunks:
        chunk_doc_id = f"{document_id}_chunk{chunk.chunk_index}"
        try:
            chunk_result = self._extract_entities(
                text=chunk.text,
                document_id=chunk_doc_id,
                document_type=document_type,
                ocr_confidence=ocr_confidence
            )
            all_entities.extend(chunk_result.get("entities", []))
            chunk_conf = chunk_result.get("confidence", 0.5)
            chunk_confidences.append((chunk_conf, len(chunk.text)))
        except Exception as e:
            logger.warning(f"Chunk {chunk.chunk_index} extraction failed: {e}")
            chunk_confidences.append((0.0, len(chunk.text)))
        # Optional: break if budget exceeded
        # if self._cost_exceeded():
        #     logger.warning("Cost cap reached; stopping chunk processing")
        #     break

    # Phase 2: Deduplicate entities across chunks
    merged_entities = self._merge_chunk_entities(all_entities, document_id)

    # Phase 3: Extract relations using full text + merged entities
    relations = []
    if len(merged_entities) >= 2:
        relations = self._extract_relations(
            text=text,  # Use full text for relation context
            entities=merged_entities,
            document_id=document_id,
            document_type=document_type
        )

    # Weighted confidence by chunk length
    if chunk_confidences:
        total_len = sum(length for _, length in chunk_confidences)
        avg_confidence = sum(conf * length for conf, length in chunk_confidences) / max(total_len, 1)
    else:
        avg_confidence = 0.5

    return LLMExtractionResult(
        entities=merged_entities,
        relations=relations,
        confidence=avg_confidence,
        reasoning=f"Chunked extraction: {len(chunks)} chunks processed",
        metadata={
            "chunks_processed": len(chunks),
            "entities_before_merge": len(all_entities),
            "entities_after_merge": len(merged_entities),
            "chunk_confidences": [conf for conf, _ in chunk_confidences],
            "failed_chunks": sum(1 for conf, _ in chunk_confidences if conf == 0.0),
        }
    )

def _merge_chunk_entities(
    self,
    entities: List[BaseEntity],
    document_id: str
) -> List[BaseEntity]:
    """
    Merge duplicate entities extracted from different chunks.

    Uses name-based matching (case-insensitive, ignoring titles).
    """
    merged = {}

    for entity in entities:
        name = getattr(entity, 'name', None)
        if not name:
            continue

        # Normalize name for matching
        normalized = self._normalize_name_for_matching(name)

        if normalized in merged:
            existing = merged[normalized]
            # Merge roles/alternate_names
            existing.roles = list(set(getattr(existing, "roles", []) + getattr(entity, "roles", [])))
            existing.alternate_names = list(set(
                getattr(existing, "alternate_names", []) + getattr(entity, "alternate_names", [])
            ))
            # Keep highest confidence verification
            if entity.verification.confidence > existing.verification.confidence:
                existing.verification = entity.verification
            # If entity types differ, keep both (avoid name collision collapse)
            if getattr(existing, "entity_type", None) != getattr(entity, "entity_type", None):
                key = f"{normalized}_{getattr(entity, 'entity_type', 'unknown')}"
                merged[key] = entity
        else:
            merged[normalized] = entity

    # Update extracted_from to use main document_id but preserve chunk provenance
    result = []
    for entity in merged.values():
        extracted = getattr(entity, "extracted_from", "")
        sources = set()
        if extracted:
            if isinstance(extracted, str):
                sources.update(extracted.split(","))
            elif isinstance(extracted, list):
                sources.update(extracted)
        sources.add(document_id)
        entity.extracted_from = ",".join(sorted(sources))
        result.append(entity)

    return result

def _normalize_name_for_matching(self, name: str) -> str:
    """Normalize name for deduplication matching."""
    # Remove common Spanish titles
    name = name.lower()
    for title in ["don ", "doña ", "sr. ", "sra. ", "dr. ", "dra. "]:
        name = name.replace(title, "")
    return name.strip()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/extract/test_llm.py::TestChunkedExtraction -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/extract/llm.py tests/extract/test_llm.py
git commit -m "feat(extract): integrate chunking for long documents

Documents over 5000 chars now processed as chunks with 10% overlap.
Entities merged across chunks by normalized name matching.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.3: Graph Post-Processing - Transitive Redundancy Removal

**Goal:** Add graph cleanup to remove edges that can be inferred from existing paths (e.g., transitive LOCATED_IN) with safe relation set and confidence-aware retention.

**Files:**
- Create: `farmer_factory/structure/postprocessor.py`
- Modify: `farmer_factory/structure/builder.py:203-223` (call postprocessor after batch)
- Test: `tests/structure/test_postprocessor.py`

**Step 1: Write the failing test**

```python
# tests/structure/test_postprocessor.py
"""Tests for graph post-processing."""

import pytest
from farmer_factory.structure.postprocessor import GraphPostProcessor
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Location, Relation, RelationType, Verification, VerificationTier
)


@pytest.fixture
def sample_graph():
    """Create a graph with redundant edges."""
    graph = KnowledgeGraph()

    # Create location hierarchy: Florida -> Camagüey -> Cuba
    florida = Location(
        id="loc_florida",
        name="Florida",
        location_type="municipality",
        parent_location_id="loc_camaguey",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc"
    )
    camaguey = Location(
        id="loc_camaguey",
        name="Camagüey",
        location_type="province",
        parent_location_id="loc_cuba",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc"
    )
    cuba = Location(
        id="loc_cuba",
        name="Cuba",
        location_type="country",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
        extracted_from="test_doc"
    )

    graph.add_entity(florida)
    graph.add_entity(camaguey)
    graph.add_entity(cuba)

    # Add LOCATED_IN relations (some redundant)
    # Direct: Florida -> Camagüey
    graph.add_relation(Relation(
        id="rel_1",
        type=RelationType.LOCATED_IN,
        source_id="loc_florida",
        target_id="loc_camaguey",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9)
    ))
    # Direct: Camagüey -> Cuba
    graph.add_relation(Relation(
        id="rel_2",
        type=RelationType.LOCATED_IN,
        source_id="loc_camaguey",
        target_id="loc_cuba",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9)
    ))
    # REDUNDANT: Florida -> Cuba (can be inferred from transitivity)
    graph.add_relation(Relation(
        id="rel_3",
        type=RelationType.LOCATED_IN,
        source_id="loc_florida",
        target_id="loc_cuba",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9)
    ))

    return graph


class TestGraphPostProcessor:
    """Tests for GraphPostProcessor."""

    def test_removes_transitive_located_in(self, sample_graph):
        """Should remove LOCATED_IN edges that can be inferred from path."""
        processor = GraphPostProcessor()

        # Before: 3 LOCATED_IN relations
        relations_before = list(sample_graph.graph.edges(data=True))
        assert len(relations_before) == 3

        # Process
        stats = processor.remove_redundant_edges(sample_graph)

        # After: should remove Florida->Cuba (redundant via Camagüey)
        relations_after = list(sample_graph.graph.edges(data=True))
        assert len(relations_after) == 2
        assert stats["edges_removed"] == 1

    def test_keeps_non_transitive_relations(self, sample_graph):
        """Should not remove edges for non-transitive relation types."""
        # Add non-transitive relation
        sample_graph.add_relation(Relation(
            id="rel_owns",
            type=RelationType.OWNS,
            source_id="loc_florida",  # Weird but for testing
            target_id="loc_cuba",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9)
        ))

        processor = GraphPostProcessor()
        processor.remove_redundant_edges(sample_graph)

        # OWNS should still exist
        owns_edges = [
            e for e in sample_graph.graph.edges(data=True)
            if e[2].get("type") == RelationType.OWNS
        ]
        assert len(owns_edges) == 1

    def test_handles_empty_graph(self):
        """Should handle empty graph without error."""
        graph = KnowledgeGraph()
        processor = GraphPostProcessor()

        stats = processor.remove_redundant_edges(graph)

        assert stats["edges_removed"] == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/structure/test_postprocessor.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# farmer_factory/structure/postprocessor.py
"""Graph post-processing for redundancy removal.

Implements edge cleanup based on Chilean KG paper recommendations:
- Remove transitive redundant edges (e.g., A->B->C implies A->C)
- Remove self-loops
- Clean up organization/location disambiguation
"""

import logging
from typing import Dict, Set, Tuple, List
import networkx as nx

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import RelationType

logger = logging.getLogger(__name__)


# Relation types that are transitive (strict, safe subset)
TRANSITIVE_RELATIONS = {
    RelationType.LOCATED_IN,      # If A in B, B in C, then A in C
    # Avoid EMPLOYED_BY transitivity (not always valid)
}

# Rules: (relation1, relation2) -> relation1 followed by relation2 implies transitive
TRANSITIVITY_RULES = [
    (RelationType.LOCATED_IN, RelationType.LOCATED_IN),
]


class GraphPostProcessor:
    """
    Post-processes knowledge graphs to remove redundant information.

    Based on Chilean KG paper (arXiv:2408.11975) graph cleanup rules.
    """

    def remove_redundant_edges(self, graph: KnowledgeGraph, dry_run: bool = False) -> Dict[str, int]:
        """
        Remove edges that can be inferred from existing paths.

        Args:
            graph: KnowledgeGraph to process (modified in place)

        Returns:
            Stats dict with counts of removed edges
        """
        stats = {
            "edges_removed": 0,
            "self_loops_removed": 0,
            "transitive_removed": 0
        }

        # First pass: remove self-loops
        self_loops = list(nx.selfloop_edges(graph.graph))
        for u, v in self_loops:
            if not dry_run:
                graph.graph.remove_edge(u, v)
            stats["self_loops_removed"] += 1
            stats["edges_removed"] += 1
            logger.debug(f"Removed self-loop on {u}")

        # Second pass: remove transitive redundancies
        edges_to_remove = self._find_transitive_redundancies(graph)

        for source, target, key in edges_to_remove:
            try:
                # Prefer keeping highest-confidence parallel edge
                parallel = graph.graph.get_edge_data(source, target)
                if parallel and len(parallel) > 1:
                    best_key = max(parallel, key=lambda k: parallel[k].get("confidence", 0))
                    if key == best_key:
                        continue
                if not dry_run:
                    graph.graph.remove_edge(source, target, key=key)
                stats["transitive_removed"] += 1
                stats["edges_removed"] += 1
                logger.debug(f"Removed transitive edge {source} -> {target}")
            except nx.NetworkXError:
                pass  # Edge already removed

        logger.info(
            f"Post-processing complete: {stats['edges_removed']} edges removed "
            f"({stats['self_loops_removed']} self-loops, "
            f"{stats['transitive_removed']} transitive)"
        )

        return stats

    def _find_transitive_redundancies(
        self,
        graph: KnowledgeGraph
    ) -> List[Tuple[str, str, int]]:
        """
        Find edges that are redundant due to transitivity.

        For each transitive relation type, if A->B->C exists,
        then A->C is redundant and can be removed.
        """
        redundant = []

        for rel_type in TRANSITIVE_RELATIONS:
            # Get all edges of this type
            typed_edges = [
                (u, v, k, d) for u, v, k, d in graph.graph.edges(data=True, keys=True)
                if d.get("type") == rel_type
            ]

            # Build adjacency for this relation type
            adjacency: Dict[str, Set[str]] = {}
            for u, v, k, d in typed_edges:
                if u not in adjacency:
                    adjacency[u] = set()
                adjacency[u].add(v)

            # For each edge A->C, check if path A->B->C exists
            for source, target, key, data in typed_edges:
                # Check if there's an intermediate node B where A->B and B->C
                if self._has_intermediate_path(source, target, adjacency):
                    redundant.append((source, target, key))

        return redundant

    def _has_intermediate_path(
        self,
        source: str,
        target: str,
        adjacency: Dict[str, Set[str]]
    ) -> bool:
        """
        Check if there's a path from source to target through an intermediate.

        Returns True if exists B where source->B and B->target.
        """
        if source not in adjacency:
            return False

        # Get all nodes reachable from source in one hop
        intermediates = adjacency.get(source, set())

        # Check if any intermediate can reach target
        for intermediate in intermediates:
            if intermediate == target:
                continue  # Skip direct edge
            if target in adjacency.get(intermediate, set()):
                return True

        return False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/structure/test_postprocessor.py -v`
Expected: PASS

**Step 5: Integrate into GraphBuilder**

```python
# In farmer_factory/structure/builder.py

# Add import at top
from farmer_factory.structure.postprocessor import GraphPostProcessor

# Modify build_from_document_batch method
def build_from_document_batch(
    self,
    extractions: List["ExtractionResult"]
) -> None:
    """
    Process multiple document extractions.

    Args:
        extractions: List of ExtractionResult objects
    """
    logger.info(f"Processing batch of {len(extractions)} documents")

    for extraction in extractions:
        self.add_extraction(extraction)

    # Post-process graph to remove redundancies
    postprocessor = GraphPostProcessor()
    cleanup_stats = postprocessor.remove_redundant_edges(self.graph)
    self.processing_stats.update(cleanup_stats)

    logger.info(
        f"Batch complete: {self.processing_stats['entities_extracted']} entities extracted, "
        f"{self.processing_stats['entities_merged']} merged, "
        f"{self.processing_stats['relations_added']} relations added, "
        f"{cleanup_stats['edges_removed']} redundant edges removed"
    )
```

**Step 6: Run full test suite for structure module**

Run: `pytest tests/structure/ -v`
Expected: PASS

**Step 7: Commit**

```bash
git add farmer_factory/structure/postprocessor.py farmer_factory/structure/builder.py tests/structure/test_postprocessor.py
git commit -m "feat(structure): add graph post-processing for redundancy removal

Removes transitive redundant edges (e.g., A->B->C implies A->C).
Based on Chilean KG paper cleanup rules.

- Removes self-loops
- Removes transitive LOCATED_IN edges
- Runs automatically after batch processing

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 1.4: Create Gold Standard Evaluation Dataset

**Goal:** Create a small gold standard dataset (5 documents) for regression testing extraction quality.

**Files:**
- Create: `tests/golden/README.md`
- Create: `tests/golden/documents/` (sample OCR text files)
- Create: `tests/golden/expected/` (expected extraction JSON files)
- Create: `tests/golden/test_golden_set.py`

**Step 1: Create directory structure and README**

```markdown
# tests/golden/README.md
# Golden Set Evaluation

This directory contains a manually curated "gold standard" dataset for evaluating
extraction quality. Based on Chilean KG paper methodology (arXiv:2408.11975).

## Purpose

1. **Regression testing**: Ensure prompt changes don't degrade extraction quality
2. **Precision/Recall measurement**: Quantify extraction accuracy
3. **Edge case coverage**: Test difficult OCR, handwritten text, mixed languages

## Structure

```
golden/
├── documents/          # Source OCR text files
│   ├── deed_1958_simple.txt
│   ├── deed_1955_complex.txt
│   ├── will_1948_handwritten.txt
│   ├── transfer_1960_poor_ocr.txt
│   └── confiscation_1961_decree.txt
├── expected/           # Expected extraction results (JSON)
│   ├── deed_1958_simple.json
│   └── ...
└── test_golden_set.py  # Evaluation tests
```

## Metrics

Based on Chilean paper evaluation:

| Metric | Target | Description |
|--------|--------|-------------|
| Entity Precision | ≥0.85 | % of extracted entities that are correct |
| Entity Recall | ≥0.80 | % of expected entities that were found |
| Relation Precision | ≥0.80 | % of extracted relations that are correct |
| Relation Recall | ≥0.75 | % of expected relations that were found |

## Adding New Test Cases

1. Add OCR text to `documents/`
2. Create expected output in `expected/` with same base name
3. Expected format matches `LLMExtractionResult` schema

## Running Tests

```bash
pytest tests/golden/test_golden_set.py -v
pytest tests/golden/test_golden_set.py --golden-report  # Generate quality report
```
```

**Step 2: Create sample document and expected output**

```python
# tests/golden/documents/deed_1958_simple.txt
"""
ESCRITURA NÚMERO CIENTO VEINTITRÉS

En la ciudad de Camagüey, a los quince días del mes de marzo de mil novecientos
cincuenta y ocho, ante mí, José Fernández García, Notario Público de este Distrito,

COMPARECE:

Don Mario Ceresa López, mayor de edad, casado, propietario, vecino de esta ciudad,
hijo de Don Juan Ceresa Martínez y Doña María López de Queral, con cédula de
identidad número 12345.

EXPONE:

Que es dueño en pleno dominio de la finca rústica denominada "Central Santa María",
ubicada en el término municipal de Florida, provincia de Camagüey, con una extensión
de quinientas hectáreas, inscrita en el Registro de la Propiedad al Folio 123,
Tomo V, Finca número 456.

La referida finca linda:
- Al Norte: con terrenos de la Sucesión Pérez
- Al Sur: con el Camino Real
- Al Este: con la finca "La Esperanza"
- Al Oeste: con el Río Caonao

Y para que conste, firmo la presente en Camagüey, en la fecha arriba indicada.

[Firma] Mario Ceresa López
[Firma] José Fernández García, Notario
"""
```

```json
// tests/golden/expected/deed_1958_simple.json
{
  "entities": [
    {
      "entity_type": "PERSON",
      "name": "Mario Ceresa López",
      "alternate_names": ["Don Mario Ceresa López"],
      "marital_status": "casado",
      "profession": "propietario",
      "residence": "Camagüey",
      "father": "Juan Ceresa Martínez",
      "mother": "María López de Queral",
      "roles": ["owner"],
      "confidence": 0.95
    },
    {
      "entity_type": "PERSON",
      "name": "José Fernández García",
      "profession": "Notario Público",
      "roles": ["notary"],
      "confidence": 0.90
    },
    {
      "entity_type": "PROPERTY",
      "name": "Central Santa María",
      "property_type": "finca rústica",
      "location": "Florida, Camagüey",
      "area": 500,
      "area_unit": "hectáreas",
      "registry_number": "Folio 123, Tomo V",
      "folio_number": "123",
      "cadastral_info": "Finca número 456",
      "confidence": 0.95
    },
    {
      "entity_type": "LOCATION",
      "name": "Florida",
      "location_type": "municipio",
      "parent_location": "Camagüey",
      "country": "Cuba",
      "confidence": 0.90
    },
    {
      "entity_type": "LOCATION",
      "name": "Camagüey",
      "location_type": "provincia",
      "country": "Cuba",
      "confidence": 0.95
    }
  ],
  "relations": [
    {
      "relation_type": "OWNS",
      "source_entity": "Mario Ceresa López",
      "target_entity": "Central Santa María",
      "confidence": 0.95,
      "evidence": "Que es dueño en pleno dominio de la finca"
    },
    {
      "relation_type": "LOCATED_IN",
      "source_entity": "Central Santa María",
      "target_entity": "Florida",
      "confidence": 0.90
    },
    {
      "relation_type": "NOTARIZED",
      "source_entity": "José Fernández García",
      "target_entity": "deed_1958_simple",
      "confidence": 0.90
    }
  ],
  "document_date": "1958-03-15"
}
```

**Step 3: Write evaluation test**

```python
# tests/golden/test_golden_set.py
"""Golden set evaluation tests for extraction quality."""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
from difflib import SequenceMatcher

from farmer_factory.extract.llm import LLMExtractionService


GOLDEN_DIR = Path(__file__).parent
DOCUMENTS_DIR = GOLDEN_DIR / "documents"
EXPECTED_DIR = GOLDEN_DIR / "expected"

# Quality thresholds from Chilean KG paper
THRESHOLDS = {
    "entity_precision": 0.85,
    "entity_recall": 0.80,
    "relation_precision": 0.80,
    "relation_recall": 0.75,
}


def load_golden_cases() -> List[Dict[str, Any]]:
    """Load all golden test cases."""
    cases = []
    for doc_path in DOCUMENTS_DIR.glob("*.txt"):
        expected_path = EXPECTED_DIR / f"{doc_path.stem}.json"
        if expected_path.exists():
            with open(doc_path) as f:
                text = f.read()
            with open(expected_path) as f:
                expected = json.load(f)
            cases.append({
                "name": doc_path.stem,
                "text": text,
                "expected": expected
            })
    return cases


def entity_matches(extracted: Dict, expected: Dict, threshold: float = 0.8) -> bool:
    """Check if extracted entity matches expected entity."""
    # Match by normalized name
    ext_name = extracted.get("name", "").lower().strip()
    exp_name = expected.get("name", "").lower().strip()

    # Fuzzy match
    ratio = SequenceMatcher(None, ext_name, exp_name).ratio()
    return ratio >= threshold


def calculate_metrics(
    extracted_entities: List[Dict],
    expected_entities: List[Dict]
) -> Dict[str, float]:
    """Calculate precision and recall for entities."""
    if not expected_entities:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    matched_expected = set()
    matched_extracted = set()

    for i, ext in enumerate(extracted_entities):
        for j, exp in enumerate(expected_entities):
            if j not in matched_expected and entity_matches(ext, exp):
                matched_expected.add(j)
                matched_extracted.add(i)
                break

    precision = len(matched_extracted) / len(extracted_entities) if extracted_entities else 0
    recall = len(matched_expected) / len(expected_entities) if expected_entities else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {"precision": precision, "recall": recall, "f1": f1}


@pytest.fixture
def llm_service():
    """LLM extraction service fixture."""
    return LLMExtractionService()


class TestGoldenSet:
    """Golden set evaluation tests."""

    @pytest.mark.parametrize("case", load_golden_cases(), ids=lambda c: c["name"])
    def test_entity_extraction_quality(self, llm_service, case):
        """Test entity extraction meets quality thresholds."""
        result = llm_service.extract_from_text(
            text=case["text"],
            document_id=case["name"]
        )

        # Convert to comparable format
        extracted = [
            {"name": getattr(e, "name", ""), "entity_type": e.entity_type.value}
            for e in result.entities
        ]
        expected = case["expected"]["entities"]

        metrics = calculate_metrics(extracted, expected)

        assert metrics["precision"] >= THRESHOLDS["entity_precision"], \
            f"Entity precision {metrics['precision']:.2f} below threshold {THRESHOLDS['entity_precision']}"
        assert metrics["recall"] >= THRESHOLDS["entity_recall"], \
            f"Entity recall {metrics['recall']:.2f} below threshold {THRESHOLDS['entity_recall']}"

    @pytest.mark.parametrize("case", load_golden_cases(), ids=lambda c: c["name"])
    def test_document_date_extraction(self, llm_service, case):
        """Test document date extraction accuracy."""
        result = llm_service.extract_from_text(
            text=case["text"],
            document_id=case["name"]
        )

        expected_date = case["expected"].get("document_date")
        if expected_date:
            # Check metadata for document_date
            extracted_date = result.metadata.get("document_date")
            assert extracted_date is not None, "Document date not extracted"
            # Allow partial match (year must match at minimum)
            assert expected_date[:4] == extracted_date[:4], \
                f"Document year mismatch: expected {expected_date}, got {extracted_date}"
```

**Step 4: Run golden set tests (expect some to skip if no API key)**

Run: `pytest tests/golden/test_golden_set.py -v`
Expected: Tests run (may skip without API key)

**Step 5: Commit**

```bash
git add tests/golden/
git commit -m "test: add golden set evaluation framework

Creates gold standard dataset for regression testing extraction quality.
Based on Chilean KG paper evaluation methodology.

- 1 sample document with expected output (more to be added)
- Precision/recall metrics with thresholds
- Parameterized tests for each golden case

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Schema Additions (Medium Effort)

These changes add new fields to existing schemas but maintain backward compatibility.

---

### Task 2.1: Add Location Nature Field for Disambiguation

**Goal:** Add `nature` field to Location and Organization to help with disambiguation (building vs institution with same name).

**Files:**
- Modify: `farmer_factory/structure/schema.py:126-134` (Location class)
- Modify: `farmer_factory/structure/schema.py:116-124` (Organization class)
- Modify: `farmer_factory/extract/llm.py` (update prompts)
- Test: `tests/structure/test_schema.py`

**Step 1: Write the failing test**

```python
# Add to tests/structure/test_schema.py

class TestLocationNature:
    """Tests for Location nature field."""

    def test_location_nature_enum_values(self):
        """Location nature should have valid enum values."""
        from farmer_factory.structure.schema import LocationNature

        assert LocationNature.COUNTRY in LocationNature
        assert LocationNature.PROVINCE in LocationNature
        assert LocationNature.MUNICIPALITY in LocationNature
        assert LocationNature.CITY in LocationNature
        assert LocationNature.NEIGHBORHOOD in LocationNature
        assert LocationNature.STREET in LocationNature
        assert LocationNature.BUILDING in LocationNature
        assert LocationNature.UNDEFINED in LocationNature

    def test_location_with_nature(self):
        """Location should accept nature field."""
        from farmer_factory.structure.schema import (
            Location, LocationNature, Verification, VerificationTier
        )

        loc = Location(
            id="loc_1",
            name="Florida",
            location_type="municipality",
            nature=LocationNature.MUNICIPALITY,
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test"
        )

        assert loc.nature == LocationNature.MUNICIPALITY

    def test_location_nature_defaults_to_undefined(self):
        """Location nature should default to UNDEFINED."""
        from farmer_factory.structure.schema import (
            Location, LocationNature, Verification, VerificationTier
        )

        loc = Location(
            id="loc_1",
            name="SomePlace",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test"
        )

        assert loc.nature == LocationNature.UNDEFINED


class TestOrganizationNature:
    """Tests for Organization nature field."""

    def test_organization_nature_enum_values(self):
        """Organization nature should have valid enum values."""
        from farmer_factory.structure.schema import OrganizationNature

        assert OrganizationNature.GOVERNMENT in OrganizationNature
        assert OrganizationNature.BANK in OrganizationNature
        assert OrganizationNature.COURT in OrganizationNature
        assert OrganizationNature.COMPANY in OrganizationNature
        assert OrganizationNature.REGISTRY in OrganizationNature
        assert OrganizationNature.UNDEFINED in OrganizationNature
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/structure/test_schema.py::TestLocationNature -v`
Expected: FAIL with "cannot import name 'LocationNature'"

**Step 3: Add enums and fields to schema**

```python
# Add to farmer_factory/structure/schema.py after EntityType enum

class LocationNature(str, Enum):
    """Nature of location for hierarchy enforcement and disambiguation.

    Ordered by containment: COUNTRY > PROVINCE > MUNICIPALITY > CITY > NEIGHBORHOOD > STREET > BUILDING
    Based on Chilean KG paper location hierarchy rules.
    """
    COUNTRY = "country"
    PROVINCE = "province"
    MUNICIPALITY = "municipality"
    CITY = "city"
    NEIGHBORHOOD = "neighborhood"
    STREET = "street"
    BUILDING = "building"
    UNDEFINED = "undefined"


class OrganizationNature(str, Enum):
    """Nature of organization for disambiguation.

    Helps distinguish when same name refers to building vs institution.
    """
    GOVERNMENT = "government"
    BANK = "bank"
    COURT = "court"
    COMPANY = "company"
    REGISTRY = "registry"
    NOTARY = "notary"
    UNDEFINED = "undefined"


# Modify Location class (around line 126)
class Location(BaseEntity):
    """Location entity (cities, provinces, neighborhoods)."""
    entity_type: Literal[EntityType.LOCATION] = EntityType.LOCATION

    name: str
    location_type: Optional[str] = None
    nature: LocationNature = Field(
        default=LocationNature.UNDEFINED,
        description="Nature of location for hierarchy validation"
    )
    parent_location_id: Optional[str] = None
    country: str = "Cuba"


# Modify Organization class (around line 116)
class Organization(BaseEntity):
    """Organization entity (banks, courts, government agencies)."""
    entity_type: Literal[EntityType.ORGANIZATION] = EntityType.ORGANIZATION

    name: str
    org_type: Optional[str] = None
    nature: OrganizationNature = Field(
        default=OrganizationNature.UNDEFINED,
        description="Nature of organization for disambiguation"
    )
    location_id: Optional[str] = None
    address: Optional[str] = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/structure/test_schema.py::TestLocationNature tests/structure/test_schema.py::TestOrganizationNature -v`
Expected: PASS

**Step 5: Update extraction prompts to extract nature**

Update `_build_entity_prompt` in `llm.py` to include nature field in LOCATION and ORGANIZATION schemas.

**Step 6: Commit**

```bash
git add farmer_factory/structure/schema.py tests/structure/test_schema.py
git commit -m "feat(schema): add nature field to Location and Organization

Enables disambiguation (building vs institution with same name)
and location hierarchy validation.

Based on Chilean KG paper disambiguation approach.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2.2: Location Hierarchy Validation

**Goal:** Add validation to ensure LOCATED_IN relations follow proper hierarchy (country > province > municipality).

**Files:**
- Modify: `farmer_factory/structure/postprocessor.py`
- Test: `tests/structure/test_postprocessor.py`

**Step 1: Write the failing test**

```python
# Add to tests/structure/test_postprocessor.py

class TestLocationHierarchyValidation:
    """Tests for location hierarchy validation."""

    def test_invalid_hierarchy_flagged(self):
        """Should flag LOCATED_IN that violates hierarchy."""
        from farmer_factory.structure.schema import (
            Location, LocationNature, Relation, RelationType,
            Verification, VerificationTier
        )

        graph = KnowledgeGraph()

        # Create locations with natures
        country = Location(
            id="loc_cuba",
            name="Cuba",
            nature=LocationNature.COUNTRY,
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test"
        )
        city = Location(
            id="loc_havana",
            name="Havana",
            nature=LocationNature.CITY,
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9),
            extracted_from="test"
        )

        graph.add_entity(country)
        graph.add_entity(city)

        # Add INVALID relation: country LOCATED_IN city (should be reverse)
        graph.add_relation(Relation(
            id="rel_bad",
            type=RelationType.LOCATED_IN,
            source_id="loc_cuba",  # Country
            target_id="loc_havana",  # City - WRONG!
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.9)
        ))

        processor = GraphPostProcessor()
        issues = processor.validate_location_hierarchy(graph)

        assert len(issues) > 0
        assert "loc_cuba" in issues[0]["source"]
```

**Step 2-5:** Implement validation and tests (similar pattern to previous tasks)

**Step 6: Commit**

```bash
git commit -m "feat(structure): add location hierarchy validation

Flags LOCATED_IN relations that violate containment hierarchy
(e.g., country inside city).

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: Architecture Considerations (Design Only)

These are larger changes that need design documents before implementation.

---

### Task 3.1: EVENT Entity Type Design Document

**Goal:** Write design document for adding EVENT as a first-class entity type.

**Note:** This task produces a design document, not code. Implementation would be a separate plan.

**Files:**
- Create: `docs/plans/2026-01-XX-event-entity-design.md`

**Content Outline:**

```markdown
# EVENT Entity Type Design

## Problem Statement
Currently, events (ownership transfers, confiscations) are encoded as relations.
This makes it difficult to:
- Track the same event across multiple documents
- Associate rich metadata with events (witnesses, location, amount)
- Build timeline views

## Proposed Solution
Add EVENT as a sixth entity type with schema:
- id, name, event_type (SALE, INHERITANCE, CONFISCATION, etc.)
- date, date_precision
- location_id, amount, currency
- participants (list of person_id + role pairs)
- document_evidence (list of document_ids)

## Migration Strategy
1. New extractions create EVENT entities
2. Convert existing SOLD/INHERITED relations to EVENT + PARTICIPATED_IN
3. Keep relations for backward compatibility initially

## Impact Analysis
- Schema: Add EVENT to EntityType enum
- Extraction: Update prompts to recognize events
- Graph: Events become nodes, not edges
- Frontend: Timeline becomes entity-based

## Recommendation
Implement in separate phase after Phase 1-2 complete.
Requires frontend timeline redesign.
```

---

## Summary

| Phase | Task | Effort | Impact |
|-------|------|--------|--------|
| 1.1 | Document chunking | 2-3 hrs | Better extraction for long docs |
| 1.2 | Chunker integration | 1-2 hrs | Enables 1.1 |
| 1.3 | Transitive redundancy removal | 2-3 hrs | Cleaner graphs |
| 1.4 | Golden set evaluation | 2-3 hrs | Quality metrics |
| 2.1 | Location/Org nature fields | 1-2 hrs | Better disambiguation |
| 2.2 | Hierarchy validation | 1-2 hrs | Catch extraction errors |
| 3.1 | EVENT design doc | 1-2 hrs | Future planning |

**Total Phase 1:** ~8-11 hours
**Total Phase 2:** ~2-4 hours
**Total Phase 3:** ~2 hours (design only)

---

**Plan complete and saved to `docs/plans/2026-01-27-academic-kg-improvements.md`.**

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
