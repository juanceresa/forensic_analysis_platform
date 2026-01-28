# Contextual Narrative Generation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build user-driven contextual narrative generation with forensic intelligence narratives featuring inline citations, conflict detection, and smart model selection.

**Architecture:** New `farmer_factory/narrative/` module with graph constellation analysis, story centrality scoring, two-stage LLM generation (fact extraction → narrative synthesis), and session-scoped Redis caching with graph-state invalidation.

**Tech Stack:** Python 3.10+, Pydantic, NetworkX, Anthropic Claude API (Haiku/Sonnet), Redis (caching), existing KnowledgeGraph infrastructure

---

## Task 1: Module Setup and Data Models

**Files:**
- Create: `farmer_factory/narrative/__init__.py`
- Create: `farmer_factory/narrative/models.py`
- Create: `tests/narrative/__init__.py`
- Create: `tests/narrative/test_models.py`

**Step 1: Write failing test for EvidenceCitation model**

Create `tests/narrative/test_models.py`:

```python
"""Tests for narrative generation data models."""

import pytest
from datetime import datetime
from farmer_factory.narrative.models import (
    EvidenceCitation,
    ConflictingClaim,
    FactualClaim,
    NarrativeResult
)
from farmer_factory.structure.schema import VerificationTier


def test_evidence_citation_creation():
    """Test EvidenceCitation model creation."""
    citation = EvidenceCitation(
        doc_id="doc_001",
        page=2,
        quote="Mario Ceresa, propietario de Villa Aurelia",
        confidence=0.92,
        verification_tier=VerificationTier.TIER_2_ANALYST,
        ocr_confidence=0.88
    )

    assert citation.doc_id == "doc_001"
    assert citation.page == 2
    assert citation.confidence == 0.92
    assert citation.verification_tier == VerificationTier.TIER_2_ANALYST


def test_evidence_citation_without_page():
    """Test EvidenceCitation with optional page."""
    citation = EvidenceCitation(
        doc_id="doc_002",
        quote="confiscada por el estado",
        confidence=0.74,
        verification_tier=VerificationTier.TIER_3_AI
    )

    assert citation.page is None
    assert citation.ocr_confidence is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_models.py::test_evidence_citation_creation -v`
Expected: FAIL with "No module named 'farmer_factory.narrative'"

**Step 3: Create module and models**

Create `farmer_factory/narrative/__init__.py`:

```python
"""Contextual narrative generation module."""

from .models import (
    EvidenceCitation,
    ConflictingClaim,
    FactualClaim,
    NarrativeResult
)

__all__ = [
    "EvidenceCitation",
    "ConflictingClaim",
    "FactualClaim",
    "NarrativeResult"
]
```

Create `farmer_factory/narrative/models.py`:

```python
"""Pydantic models for narrative generation output."""

from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field

from farmer_factory.structure.schema import VerificationTier


class EvidenceCitation(BaseModel):
    """Single piece of evidence supporting a claim."""

    doc_id: str = Field(description="Source document ID")
    page: Optional[int] = Field(default=None, description="Page number in document")
    quote: str = Field(description="Exact quote from document")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    verification_tier: VerificationTier = Field(description="Verification tier")
    ocr_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="OCR quality score"
    )


class ConflictingClaim(BaseModel):
    """Competing versions of a factual claim."""

    claim_summary: str = Field(description="Brief description (e.g., 'Sale date')")
    versions: List[EvidenceCitation] = Field(
        description="Competing evidence citations",
        min_length=2
    )
    resolution: str = Field(
        description="How conflict was resolved (e.g., 'Using highest confidence')"
    )
    citation_number: int = Field(description="Citation number in narrative")


class FactualClaim(BaseModel):
    """Single fact in the narrative with supporting evidence."""

    claim_text: str = Field(description="The factual claim statement")
    citation_number: int = Field(description="Citation reference number")
    evidence: List[EvidenceCitation] = Field(
        description="Supporting evidence",
        min_length=1
    )
    temporal_context: Optional[str] = Field(
        default=None,
        description="Date/time context (e.g., '1956', 'Early 1960s')"
    )
    fact_type: Optional[str] = Field(
        default=None,
        description="Fact category (e.g., 'OWNERSHIP', 'TRANSFER', 'CONFISCATION')"
    )


class NarrativeResult(BaseModel):
    """Complete narrative generation result."""

    # Metadata
    focal_entity_id: str = Field(description="ID of narrative focal point")
    focal_entity_name: str = Field(description="Name of focal entity")
    focal_entity_type: str = Field(description="Entity type (PROPERTY, PERSON, etc)")
    constellation_size: int = Field(description="Number of entities in context")
    generated_at: datetime = Field(default_factory=datetime.now)
    model_used: Literal["haiku", "sonnet"] = Field(description="LLM model used")

    # Content
    main_narrative: str = Field(
        description="Chronological narrative with inline citations [①]"
    )
    facts: List[FactualClaim] = Field(description="Structured factual claims")
    conflicts: List[ConflictingClaim] = Field(
        default_factory=list,
        description="Conflicting claims detected"
    )

    # Quality indicators
    total_documents: int = Field(description="Number of source documents")
    total_citations: int = Field(description="Total evidence citations")
    date_range: Optional[str] = Field(
        default=None,
        description="Temporal span (e.g., '1952-1962')"
    )
    confidence_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by verification tier"
    )

    # Quality warnings
    quality_warning: Optional[str] = Field(
        default=None,
        description="Warning for low-quality data"
    )
    show_warning_banner: bool = Field(
        default=False,
        description="Display warning UI"
    )
    data_quality_issues: List[str] = Field(
        default_factory=list,
        description="Data quality issues detected"
    )
```

Create `tests/narrative/__init__.py` (empty file).

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_models.py -v`
Expected: PASS (2 tests)

**Step 5: Add remaining model tests**

Add to `tests/narrative/test_models.py`:

```python
def test_conflicting_claim_creation():
    """Test ConflictingClaim model."""
    claim = ConflictingClaim(
        claim_summary="Sale date",
        versions=[
            EvidenceCitation(
                doc_id="doc_007",
                page=1,
                quote="1956",
                confidence=0.89,
                verification_tier=VerificationTier.TIER_2_ANALYST
            ),
            EvidenceCitation(
                doc_id="doc_003",
                page=2,
                quote="1957",
                confidence=0.61,
                verification_tier=VerificationTier.TIER_3_AI
            )
        ],
        resolution="Using highest confidence version",
        citation_number=2
    )

    assert claim.claim_summary == "Sale date"
    assert len(claim.versions) == 2
    assert claim.versions[0].confidence > claim.versions[1].confidence


def test_factual_claim_creation():
    """Test FactualClaim model."""
    claim = FactualClaim(
        claim_text="Mario Ceresa owned Villa Aurelia",
        citation_number=1,
        evidence=[
            EvidenceCitation(
                doc_id="doc_003",
                page=2,
                quote="Mario Ceresa, propietario",
                confidence=0.92,
                verification_tier=VerificationTier.TIER_2_ANALYST
            )
        ],
        temporal_context="1952",
        fact_type="OWNERSHIP"
    )

    assert claim.claim_text == "Mario Ceresa owned Villa Aurelia"
    assert claim.temporal_context == "1952"
    assert len(claim.evidence) == 1


def test_narrative_result_creation():
    """Test NarrativeResult model."""
    result = NarrativeResult(
        focal_entity_id="prop_villa_aurelia_001",
        focal_entity_name="Villa Aurelia",
        focal_entity_type="PROPERTY",
        constellation_size=15,
        model_used="sonnet",
        main_narrative="Villa Aurelia first appears in 1952 [①].",
        facts=[
            FactualClaim(
                claim_text="First appearance",
                citation_number=1,
                evidence=[
                    EvidenceCitation(
                        doc_id="doc_003",
                        quote="Villa Aurelia",
                        confidence=0.92,
                        verification_tier=VerificationTier.TIER_2_ANALYST
                    )
                ]
            )
        ],
        total_documents=8,
        total_citations=12,
        date_range="1952-1962",
        confidence_summary={"TIER_2_ANALYST": 8, "TIER_3_AI": 4}
    )

    assert result.focal_entity_name == "Villa Aurelia"
    assert result.model_used == "sonnet"
    assert result.total_documents == 8
    assert "TIER_2_ANALYST" in result.confidence_summary
```

**Step 6: Run tests**

Run: `pytest tests/narrative/test_models.py -v`
Expected: PASS (5 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/ tests/narrative/
git commit -m "feat(narrative): add Pydantic models for narrative generation"
```

---

## Task 2: Story Centrality Scoring Algorithm

**Files:**
- Create: `farmer_factory/narrative/scorer.py`
- Create: `tests/narrative/test_scorer.py`

**Step 1: Write failing test for centrality scoring**

Create `tests/narrative/test_scorer.py`:

```python
"""Tests for story centrality scoring algorithm."""

import pytest
from farmer_factory.narrative.scorer import StoryScorer
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def sample_graph():
    """Create sample graph with property, people, and relations."""
    kg = KnowledgeGraph(case_id="test_001")

    # Property (should score highest)
    property = Property(
        id="prop_001",
        entity_type=EntityType.PROPERTY,
        name="Villa Aurelia",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.92
        ),
        extracted_from="doc_001,doc_003,doc_007"
    )
    kg.add_entity(property)

    # Owner 1
    person1 = Person(
        id="person_001",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.89
        ),
        extracted_from="doc_001,doc_003"
    )
    kg.add_entity(person1)

    # Owner 2
    person2 = Person(
        id="person_002",
        entity_type=EntityType.PERSON,
        name="Juan Ceresa",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.87
        ),
        extracted_from="doc_007"
    )
    kg.add_entity(person2)

    # Relations
    rel1 = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.90
        ),
        extracted_from="doc_001"
    )
    kg.add_relation(rel1)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.SOLD,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.88
        ),
        extracted_from="doc_007"
    )
    kg.add_relation(rel2)

    return kg


def test_scorer_initialization():
    """Test StoryScorer initialization."""
    scorer = StoryScorer()
    assert scorer is not None


def test_property_scores_highest(sample_graph):
    """Test that properties score higher than people."""
    scorer = StoryScorer()

    prop_score = scorer.calculate_centrality("prop_001", sample_graph)
    person_score = scorer.calculate_centrality("person_001", sample_graph)

    assert prop_score > person_score


def test_more_connections_increases_score(sample_graph):
    """Test that entities with more connections score higher."""
    scorer = StoryScorer()

    # prop_001 has 2 incoming relations
    # person_002 has 0 relations
    prop_score = scorer.calculate_centrality("prop_001", sample_graph)
    person_score = scorer.calculate_centrality("person_002", sample_graph)

    assert prop_score > person_score
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_scorer.py::test_scorer_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.scorer'"

**Step 3: Implement story centrality scorer**

Create `farmer_factory/narrative/scorer.py`:

```python
"""Story centrality scoring algorithm for narrative focal point selection."""

from typing import Dict, List
import logging

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import EntityType, RelationType

logger = logging.getLogger(__name__)


# Type weights: Properties are protagonists in restitution stories
TYPE_WEIGHTS = {
    EntityType.PROPERTY: 10.0,
    EntityType.LOCATION: 8.0,
    EntityType.PERSON: 5.0,
    EntityType.ORGANIZATION: 3.0,
    EntityType.DOCUMENT: 1.0
}

# Relation weights: Some matter more than others
RELATION_WEIGHTS = {
    RelationType.OWNS: 3.0,
    RelationType.SOLD: 2.5,
    RelationType.INHERITED: 2.5,
    RelationType.CONFISCATED: 2.5,
    RelationType.BOUGHT: 2.5,
    RelationType.LOCATED_IN: 1.5,
    RelationType.WITNESSED: 1.0,
    RelationType.NOTARIZED: 1.0,
    RelationType.EMPLOYED_BY: 1.0,
    RelationType.RELATED_TO: 0.5,
}


class StoryScorer:
    """Calculate story centrality scores for entities in knowledge graph."""

    def __init__(
        self,
        type_weights: Dict[EntityType, float] = None,
        relation_weights: Dict[RelationType, float] = None,
        connection_multiplier: float = 2.0,
        document_multiplier: float = 3.0
    ):
        """
        Initialize story scorer.

        Args:
            type_weights: Entity type importance weights
            relation_weights: Relation type importance weights
            connection_multiplier: Weight per graph connection
            document_multiplier: Weight per source document
        """
        self.type_weights = type_weights or TYPE_WEIGHTS
        self.relation_weights = relation_weights or RELATION_WEIGHTS
        self.connection_multiplier = connection_multiplier
        self.document_multiplier = document_multiplier

    def calculate_centrality(
        self,
        entity_id: str,
        graph: KnowledgeGraph
    ) -> float:
        """
        Calculate story centrality score for an entity.

        Higher scores = better narrative focal points.

        Args:
            entity_id: Entity to score
            graph: Knowledge graph containing entity

        Returns:
            Centrality score (higher = more central to story)
        """
        entity_data = graph.get_entity(entity_id)
        if not entity_data:
            logger.warning(f"Entity {entity_id} not found in graph")
            return 0.0

        # Base score by entity type
        entity_type = EntityType(entity_data["entity_type"])
        base_score = self.type_weights.get(entity_type, 1.0)

        # Connection count (network importance)
        relations = graph.get_relations(entity_id, direction="both")
        connection_score = len(relations) * self.connection_multiplier

        # Document frequency (corroboration strength)
        extracted_from = entity_data.get("extracted_from", "")
        doc_count = len(extracted_from.split(",")) if extracted_from else 1
        document_score = doc_count * self.document_multiplier

        # Weighted relations (important relations matter more)
        weighted_relations = 0.0
        for relation in relations:
            rel_type_str = relation.get("relation_type", "")
            try:
                rel_type = RelationType(rel_type_str)
                weighted_relations += self.relation_weights.get(rel_type, 1.0)
            except ValueError:
                logger.debug(f"Unknown relation type: {rel_type_str}")
                weighted_relations += 1.0

        total_score = (
            base_score +
            connection_score +
            document_score +
            weighted_relations
        )

        logger.debug(
            f"Entity {entity_id} centrality: {total_score:.2f} "
            f"(base={base_score}, conn={connection_score}, "
            f"doc={document_score}, rel={weighted_relations})"
        )

        return total_score

    def rank_entities(
        self,
        entity_ids: List[str],
        graph: KnowledgeGraph
    ) -> List[tuple[str, float]]:
        """
        Rank entities by story centrality.

        Args:
            entity_ids: Entities to rank
            graph: Knowledge graph

        Returns:
            List of (entity_id, score) tuples, sorted highest to lowest
        """
        scores = [
            (entity_id, self.calculate_centrality(entity_id, graph))
            for entity_id in entity_ids
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_scorer.py -v`
Expected: PASS (3 tests)

**Step 5: Add edge case tests**

Add to `tests/narrative/test_scorer.py`:

```python
def test_scorer_handles_missing_entity():
    """Test scorer handles missing entity gracefully."""
    kg = KnowledgeGraph(case_id="test_001")
    scorer = StoryScorer()

    score = scorer.calculate_centrality("nonexistent_001", kg)
    assert score == 0.0


def test_rank_entities(sample_graph):
    """Test ranking multiple entities."""
    scorer = StoryScorer()

    entity_ids = ["prop_001", "person_001", "person_002"]
    ranked = scorer.rank_entities(entity_ids, sample_graph)

    # Should return list of (id, score) tuples
    assert len(ranked) == 3
    assert ranked[0][0] == "prop_001"  # Property highest

    # Scores should be descending
    assert ranked[0][1] >= ranked[1][1]
    assert ranked[1][1] >= ranked[2][1]
```

**Step 6: Run tests**

Run: `pytest tests/narrative/test_scorer.py -v`
Expected: PASS (5 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/scorer.py tests/narrative/test_scorer.py
git commit -m "feat(narrative): implement story centrality scoring algorithm"
```

---

## Task 3: Constellation Analysis (Graph Component Extraction)

**Files:**
- Create: `farmer_factory/narrative/constellation.py`
- Create: `tests/narrative/test_constellation.py`

**Step 1: Write failing test for constellation extraction**

Create `tests/narrative/test_constellation.py`:

```python
"""Tests for constellation analysis (connected component extraction)."""

import pytest
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def multi_component_graph():
    """Graph with two separate constellations."""
    kg = KnowledgeGraph(case_id="test_001")

    # Constellation 1: Villa Aurelia + owners
    prop1 = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_entity(prop1)

    person1 = Person(
        id="person_001",
        name="Mario Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_entity(person1)

    rel1 = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001"
    )
    kg.add_relation(rel1)

    # Constellation 2: Separate property + owner
    prop2 = Property(
        id="prop_002",
        name="Finca Rosa",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_entity(prop2)

    person2 = Person(
        id="person_002",
        name="Rosa Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_entity(person2)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.OWNS,
        source_id="person_002",
        target_id="prop_002",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_002"
    )
    kg.add_relation(rel2)

    return kg


def test_analyzer_initialization():
    """Test ConstellationAnalyzer initialization."""
    analyzer = ConstellationAnalyzer()
    assert analyzer is not None


def test_extract_constellation(multi_component_graph):
    """Test extracting connected component around a node."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    # Should contain prop_001 and person_001, but NOT prop_002/person_002
    assert len(constellation) == 2
    assert "person_001" in constellation
    assert "prop_001" in constellation
    assert "person_002" not in constellation
    assert "prop_002" not in constellation


def test_identify_hub(multi_component_graph):
    """Test identifying narrative hub in constellation."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    hub_id = analyzer.identify_hub(
        constellation=constellation,
        graph=multi_component_graph
    )

    # Property should be identified as hub (higher centrality)
    assert hub_id == "prop_001"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_constellation.py::test_analyzer_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.constellation'"

**Step 3: Implement constellation analyzer**

Create `farmer_factory/narrative/constellation.py`:

```python
"""Constellation analysis for extracting graph components and identifying hubs."""

from typing import List, Set, Optional
import logging
import networkx as nx

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative.scorer import StoryScorer

logger = logging.getLogger(__name__)


class ConstellationAnalyzer:
    """Extract graph constellations and identify narrative focal points."""

    def __init__(self, scorer: Optional[StoryScorer] = None):
        """
        Initialize constellation analyzer.

        Args:
            scorer: Story centrality scorer (creates default if not provided)
        """
        self.scorer = scorer or StoryScorer()

    def extract_constellation(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph
    ) -> Set[str]:
        """
        Extract connected component (constellation) containing clicked node.

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph

        Returns:
            Set of entity IDs in same connected component
        """
        if not graph.graph.has_node(clicked_node_id):
            logger.warning(f"Node {clicked_node_id} not found in graph")
            return set()

        # Convert directed graph to undirected for component analysis
        undirected = graph.graph.to_undirected()

        # Find connected component containing clicked node
        for component in nx.connected_components(undirected):
            if clicked_node_id in component:
                logger.info(
                    f"Extracted constellation of {len(component)} entities "
                    f"around {clicked_node_id}"
                )
                return component

        # Isolated node
        return {clicked_node_id}

    def identify_hub(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Identify optimal narrative focal point within constellation.

        Uses story centrality scoring to find entity with highest
        narrative importance.

        Args:
            constellation: Set of entity IDs in constellation
            graph: Knowledge graph

        Returns:
            Entity ID of hub, or None if constellation empty
        """
        if not constellation:
            return None

        # Rank all entities in constellation
        ranked = self.scorer.rank_entities(
            entity_ids=list(constellation),
            graph=graph
        )

        if not ranked:
            return None

        hub_id, hub_score = ranked[0]
        logger.info(
            f"Identified hub: {hub_id} (score={hub_score:.2f}) "
            f"from {len(constellation)} candidates"
        )

        return hub_id

    def analyze(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph
    ) -> tuple[Set[str], Optional[str]]:
        """
        Full constellation analysis: extract + identify hub.

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph

        Returns:
            (constellation_ids, hub_id)
        """
        constellation = self.extract_constellation(clicked_node_id, graph)
        hub_id = self.identify_hub(constellation, graph)
        return constellation, hub_id
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_constellation.py -v`
Expected: PASS (3 tests)

**Step 5: Add complexity tests**

Add to `tests/narrative/test_constellation.py`:

```python
def test_analyze_combines_extraction_and_hub_id(multi_component_graph):
    """Test full analysis pipeline."""
    analyzer = ConstellationAnalyzer()

    constellation, hub_id = analyzer.analyze(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    assert len(constellation) == 2
    assert hub_id == "prop_001"


def test_handles_isolated_node():
    """Test handling of isolated node."""
    kg = KnowledgeGraph(case_id="test_001")

    person = Person(
        id="person_001",
        name="Isolated Person",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_001"
    )
    kg.add_entity(person)

    analyzer = ConstellationAnalyzer()
    constellation, hub_id = analyzer.analyze("person_001", kg)

    assert len(constellation) == 1
    assert hub_id == "person_001"


def test_handles_missing_node():
    """Test handling of nonexistent node."""
    kg = KnowledgeGraph(case_id="test_001")
    analyzer = ConstellationAnalyzer()

    constellation, hub_id = analyzer.analyze("nonexistent_001", kg)

    assert len(constellation) == 0
    assert hub_id is None
```

**Step 6: Run tests**

Run: `pytest tests/narrative/test_constellation.py -v`
Expected: PASS (6 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/constellation.py tests/narrative/test_constellation.py
git commit -m "feat(narrative): implement constellation analysis and hub identification"
```

---

## Task 4: Narrative Generation Prompts

**Files:**
- Create: `farmer_factory/narrative/prompts.py`
- Create: `tests/narrative/test_prompts.py`

**Step 1: Write test for prompt construction**

Create `tests/narrative/test_prompts.py`:

```python
"""Tests for narrative generation prompts."""

import pytest
from farmer_factory.narrative.prompts import NarrativePrompts


def test_prompts_initialization():
    """Test NarrativePrompts initialization."""
    prompts = NarrativePrompts()
    assert prompts is not None


def test_fact_extraction_prompt():
    """Test fact extraction prompt contains required constraints."""
    prompts = NarrativePrompts()

    prompt = prompts.build_fact_extraction_prompt(
        focal_entity_name="Villa Aurelia",
        focal_entity_type="PROPERTY",
        graph_context={
            "entities": ["Mario Ceresa", "Juan Ceresa"],
            "relations": ["OWNS", "SOLD"],
            "documents": ["doc_001", "doc_003"]
        }
    )

    # Should contain forensic facts constraint
    assert "forensic facts" in prompt.lower()
    # Should mention focal entity
    assert "Villa Aurelia" in prompt
    # Should constrain to documentary evidence
    assert "document" in prompt.lower()
    # Should prohibit legal conclusions
    assert "legal" in prompt.lower() or "conclusion" in prompt.lower()


def test_narrative_synthesis_prompt():
    """Test narrative synthesis prompt."""
    prompts = NarrativePrompts()

    facts = [
        {"claim": "Mario Ceresa owned Villa Aurelia in 1952", "doc": "doc_001"},
        {"claim": "Property transferred to Juan in 1956", "doc": "doc_007"}
    ]

    prompt = prompts.build_narrative_synthesis_prompt(
        focal_entity_name="Villa Aurelia",
        facts=facts
    )

    # Should contain chronological ordering instruction
    assert "chronological" in prompt.lower()
    # Should reference citations
    assert "citation" in prompt.lower() or "[①]" in prompt
    # Should mention focal entity
    assert "Villa Aurelia" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_prompts.py::test_prompts_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.prompts'"

**Step 3: Implement prompt templates**

Create `farmer_factory/narrative/prompts.py`:

```python
"""LLM prompts for narrative generation (two-stage process)."""

from typing import Dict, List, Any


class NarrativePrompts:
    """Prompt templates for narrative generation."""

    FACT_EXTRACTION_TEMPLATE = """You are a forensic analyst extracting facts from historical property records.

**CRITICAL CONSTRAINTS:**
1. Extract ONLY claims directly supported by documentary evidence
2. NEVER infer or make legal conclusions
3. NEVER assess ownership validity
4. Use past tense, factual tone only
5. Each claim must cite source document

**Focal Entity:** {focal_entity_name} ({focal_entity_type})

**Graph Context:**
{graph_context}

**Task:**
Extract all factual claims about {focal_entity_name} that are directly stated in the documents.

For each claim, provide:
- The factual statement (e.g., "Mario Ceresa owned Villa Aurelia")
- Source document ID and page
- Exact quote from document
- Date/time context if stated
- Claim type (OWNERSHIP, TRANSFER, CONFISCATION, etc.)

**Output Format:**
Return a JSON array of factual claims:
[
  {{
    "claim_text": "exact factual claim",
    "doc_id": "doc_001",
    "page": 2,
    "quote": "exact quote from document",
    "temporal_context": "1952",
    "fact_type": "OWNERSHIP"
  }}
]

If multiple documents make conflicting claims (e.g., different dates), include ALL versions.
"""

    NARRATIVE_SYNTHESIS_TEMPLATE = """You are a forensic analyst writing a chronological narrative from verified facts.

**CRITICAL CONSTRAINTS:**
1. Write in past tense, factual tone
2. EVERY claim must have inline citation: [①], [②], etc.
3. Present events in chronological order
4. When facts conflict, present highest-confidence version in main narrative
5. NEVER make legal conclusions or inferences
6. NEVER assess ownership validity

**Focal Entity:** {focal_entity_name}

**Verified Facts:**
{facts_list}

**Task:**
Write a chronological narrative about {focal_entity_name} using ONLY the verified facts above.

**Format Requirements:**
- Use inline citations: "In 1952, Mario Ceresa owned Villa Aurelia [①]."
- Start from earliest date
- Group related facts logically
- Keep it concise (3-5 paragraphs for simple entities, 5-10 for complex)

**Output:**
Return the narrative as plain text with inline citations.
"""

    CONFLICT_RESOLUTION_TEMPLATE = """You are analyzing conflicting claims from multiple documents.

**Competing Claims:**
{conflicting_claims}

**Task:**
For each conflict, provide:
1. Brief summary of what's in conflict (e.g., "Sale date")
2. All competing versions with evidence
3. Resolution approach (e.g., "Using highest confidence version")

**Output Format:**
Return JSON array of conflicts:
[
  {{
    "claim_summary": "Sale date",
    "versions": [
      {{"doc_id": "doc_007", "quote": "1956", "confidence": 0.89, "tier": "TIER_2_ANALYST"}},
      {{"doc_id": "doc_003", "quote": "1957", "confidence": 0.61, "tier": "TIER_3_AI"}}
    ],
    "resolution": "Using highest confidence version (doc_007)"
  }}
]
"""

    def build_fact_extraction_prompt(
        self,
        focal_entity_name: str,
        focal_entity_type: str,
        graph_context: Dict[str, Any]
    ) -> str:
        """
        Build prompt for fact extraction stage.

        Args:
            focal_entity_name: Name of narrative focal point
            focal_entity_type: Entity type (PROPERTY, PERSON, etc)
            graph_context: Graph data (entities, relations, documents)

        Returns:
            Formatted prompt string
        """
        # Format graph context
        entities_str = "\n".join([f"- {e}" for e in graph_context.get("entities", [])])
        relations_str = "\n".join([f"- {r}" for r in graph_context.get("relations", [])])
        docs_str = "\n".join([f"- {d}" for d in graph_context.get("documents", [])])

        context_str = f"""
**Entities in Context:**
{entities_str}

**Relation Types:**
{relations_str}

**Source Documents:**
{docs_str}
"""

        return self.FACT_EXTRACTION_TEMPLATE.format(
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            graph_context=context_str
        )

    def build_narrative_synthesis_prompt(
        self,
        focal_entity_name: str,
        facts: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for narrative synthesis stage.

        Args:
            focal_entity_name: Name of narrative focal point
            facts: List of extracted factual claims

        Returns:
            Formatted prompt string
        """
        # Format facts list with citation numbers
        facts_lines = []
        for i, fact in enumerate(facts, 1):
            fact_str = f"[{i}] {fact['claim']} (doc: {fact['doc']}"
            if fact.get('page'):
                fact_str += f", p.{fact['page']}"
            fact_str += ")"
            facts_lines.append(fact_str)

        facts_list = "\n".join(facts_lines)

        return self.NARRATIVE_SYNTHESIS_TEMPLATE.format(
            focal_entity_name=focal_entity_name,
            facts_list=facts_list
        )

    def build_conflict_resolution_prompt(
        self,
        conflicting_claims: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for conflict resolution.

        Args:
            conflicting_claims: List of conflicting fact groups

        Returns:
            Formatted prompt string
        """
        conflicts_str = "\n\n".join([
            f"Conflict {i+1}: {c}"
            for i, c in enumerate(conflicting_claims)
        ])

        return self.CONFLICT_RESOLUTION_TEMPLATE.format(
            conflicting_claims=conflicts_str
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_prompts.py -v`
Expected: PASS (3 tests)

**Step 5: Add template validation tests**

Add to `tests/narrative/test_prompts.py`:

```python
def test_conflict_resolution_prompt():
    """Test conflict resolution prompt."""
    prompts = NarrativePrompts()

    conflicts = [
        {
            "claim": "Sale date",
            "versions": [
                {"doc": "doc_007", "value": "1956"},
                {"doc": "doc_003", "value": "1957"}
            ]
        }
    ]

    prompt = prompts.build_conflict_resolution_prompt(conflicts)

    assert "conflict" in prompt.lower()
    assert "doc_007" in prompt
    assert "doc_003" in prompt


def test_prompts_prevent_legal_conclusions():
    """Test that prompts explicitly prevent legal conclusions."""
    prompts = NarrativePrompts()

    # Check all templates forbid legal conclusions
    assert "NEVER" in prompts.FACT_EXTRACTION_TEMPLATE
    assert "legal" in prompts.FACT_EXTRACTION_TEMPLATE.lower()
    assert "NEVER" in prompts.NARRATIVE_SYNTHESIS_TEMPLATE
    assert "legal" in prompts.NARRATIVE_SYNTHESIS_TEMPLATE.lower()


def test_prompts_require_citations():
    """Test that prompts require evidence citations."""
    prompts = NarrativePrompts()

    assert "citation" in prompts.FACT_EXTRACTION_TEMPLATE.lower()
    assert "citation" in prompts.NARRATIVE_SYNTHESIS_TEMPLATE.lower()
    assert "[①]" in prompts.NARRATIVE_SYNTHESIS_TEMPLATE
```

**Step 6: Run tests**

Run: `pytest tests/narrative/test_prompts.py -v`
Expected: PASS (6 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/prompts.py tests/narrative/test_prompts.py
git commit -m "feat(narrative): add LLM prompt templates for two-stage generation"
```

---

## Task 5: Model Selection Logic

**Files:**
- Modify: `farmer_factory/narrative/constellation.py`
- Create: `tests/narrative/test_model_selection.py`

**Step 1: Write test for model selection**

Create `tests/narrative/test_model_selection.py`:

```python
"""Tests for LLM model selection based on complexity."""

import pytest
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Person,
    Property,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


def test_simple_constellation_uses_haiku():
    """Test simple constellations (≤3 entities) use Haiku."""
    kg = KnowledgeGraph(case_id="test_001")

    # Simple: 2 entities, 1 relation, 1 document
    prop = Property(
        id="prop_001",
        name="Simple Property",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_001"
    )
    kg.add_entity(prop)

    person = Person(
        id="person_001",
        name="Owner",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_001"
    )
    kg.add_entity(person)

    rel = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.8),
        extracted_from="doc_001"
    )
    kg.add_relation(rel)

    analyzer = ConstellationAnalyzer()
    constellation, hub_id = analyzer.analyze("prop_001", kg)

    model = analyzer.select_model(constellation, kg)
    assert model == "haiku"


def test_complex_constellation_uses_sonnet():
    """Test complex constellations (>50 complexity) use Sonnet."""
    kg = KnowledgeGraph(case_id="test_001")

    # Create complex graph: 10 entities, multiple relations, multiple docs
    prop = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
        extracted_from="doc_001,doc_002,doc_003,doc_007,doc_012"  # 5 docs
    )
    kg.add_entity(prop)

    # Add 9 people
    for i in range(9):
        person = Person(
            id=f"person_{i:03d}",
            name=f"Person {i}",
            entity_type=EntityType.PERSON,
            verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
            extracted_from=f"doc_{i:03d}"
        )
        kg.add_entity(person)

        # Each person has relation to property
        rel = Relation(
            id=f"rel_{i:03d}",
            type=RelationType.OWNS if i % 2 == 0 else RelationType.SOLD,
            source_id=f"person_{i:03d}",
            target_id="prop_001",
            verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.9),
            extracted_from=f"doc_{i:03d}"
        )
        kg.add_relation(rel)

    analyzer = ConstellationAnalyzer()
    constellation, hub_id = analyzer.analyze("prop_001", kg)

    model = analyzer.select_model(constellation, kg)
    assert model == "sonnet"


def test_complexity_calculation():
    """Test complexity score calculation."""
    analyzer = ConstellationAnalyzer()

    # Mock constellation and graph data
    complexity = analyzer.calculate_complexity(
        entity_count=10,
        relation_count=15,
        document_count=5
    )

    # complexity = entities*2 + relations*1.5 + documents*3
    # = 10*2 + 15*1.5 + 5*3 = 20 + 22.5 + 15 = 57.5
    assert complexity == 57.5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_model_selection.py::test_simple_constellation_uses_haiku -v`
Expected: FAIL with "ConstellationAnalyzer has no attribute 'select_model'"

**Step 3: Implement model selection in ConstellationAnalyzer**

Add to `farmer_factory/narrative/constellation.py`:

```python
from typing import Literal

# Add to ConstellationAnalyzer class:

    def calculate_complexity(
        self,
        entity_count: int,
        relation_count: int,
        document_count: int
    ) -> float:
        """
        Calculate constellation complexity score.

        Args:
            entity_count: Number of entities in constellation
            relation_count: Number of relations
            document_count: Number of unique source documents

        Returns:
            Complexity score (higher = more complex)
        """
        complexity = (
            entity_count * 2.0 +
            relation_count * 1.5 +
            document_count * 3.0
        )
        return complexity

    def select_model(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph,
        complexity_threshold: float = 50.0
    ) -> Literal["haiku", "sonnet"]:
        """
        Select LLM model based on constellation complexity.

        Simple contexts use Haiku (cheap), complex use Sonnet (deep).

        Args:
            constellation: Set of entity IDs
            graph: Knowledge graph
            complexity_threshold: Complexity above which to use Sonnet

        Returns:
            "haiku" or "sonnet"
        """
        # Count entities
        entity_count = len(constellation)

        # Count relations within constellation
        all_relations = []
        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")
            # Only count relations between entities in constellation
            for rel in relations:
                source = rel.get("source")
                target = rel.get("target")
                if source in constellation and target in constellation:
                    all_relations.append(rel)

        relation_count = len(all_relations)

        # Count unique documents
        unique_docs = set()
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    docs = extracted_from.split(",")
                    unique_docs.update(docs)

        document_count = len(unique_docs)

        # Calculate complexity
        complexity = self.calculate_complexity(
            entity_count=entity_count,
            relation_count=relation_count,
            document_count=document_count
        )

        model = "sonnet" if complexity > complexity_threshold else "haiku"

        logger.info(
            f"Model selection: {model} "
            f"(complexity={complexity:.1f}, entities={entity_count}, "
            f"relations={relation_count}, docs={document_count})"
        )

        return model
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_model_selection.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add farmer_factory/narrative/constellation.py tests/narrative/test_model_selection.py
git commit -m "feat(narrative): add model selection based on complexity scoring"
```

---

## Task 6: Session Cache Implementation

**Files:**
- Create: `farmer_factory/narrative/cache.py`
- Create: `tests/narrative/test_cache.py`
- Modify: `farmer_factory/requirements.txt`

**Step 1: Add Redis dependency**

Modify `farmer_factory/requirements.txt`:

```python
# Add after line 29 (after supabase)
redis>=5.0.0  # Session caching for narrative generation
```

**Step 2: Write failing test for cache**

Create `tests/narrative/test_cache.py`:

```python
"""Tests for narrative session cache."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.cache import NarrativeCache


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('farmer_factory.narrative.cache.redis.Redis') as mock:
        redis_instance = Mock()
        mock.return_value = redis_instance
        yield redis_instance


def test_cache_initialization(mock_redis):
    """Test NarrativeCache initialization."""
    cache = NarrativeCache()
    assert cache is not None


def test_cache_key_generation():
    """Test cache key generation includes session, entity, and graph hash."""
    cache = NarrativeCache()

    key = cache.generate_cache_key(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert "sess_123" in key
    assert "prop_001" in key
    assert "abc123" in key


def test_cache_miss_returns_none(mock_redis):
    """Test cache miss returns None."""
    mock_redis.get.return_value = None

    cache = NarrativeCache()
    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result is None


def test_cache_hit_returns_data(mock_redis):
    """Test cache hit returns stored data."""
    import json
    cached_data = {"narrative": "Test narrative", "model": "haiku"}
    mock_redis.get.return_value = json.dumps(cached_data)

    cache = NarrativeCache()
    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result == cached_data


def test_cache_set_stores_data(mock_redis):
    """Test setting cache data."""
    cache = NarrativeCache()

    data = {"narrative": "Test narrative", "model": "haiku"}
    cache.set(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123",
        data=data,
        ttl=3600
    )

    mock_redis.setex.assert_called_once()
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/narrative/test_cache.py::test_cache_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.cache'"

**Step 4: Implement narrative cache**

Create `farmer_factory/narrative/cache.py`:

```python
"""Session-scoped caching for narrative generation with graph-state invalidation."""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, Set
from datetime import datetime

import redis

from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class NarrativeCache:
    """Redis-backed cache for narrative generation with graph-aware invalidation."""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        default_ttl: int = 3600  # 1 hour
    ):
        """
        Initialize narrative cache.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.default_ttl = default_ttl

    def generate_cache_key(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> str:
        """
        Generate cache key.

        Cache invalidates when:
        - Different session
        - Different focal entity
        - Graph state changes (hash changes)

        Args:
            session_id: User session ID
            focal_entity_id: Narrative focal point
            graph_hash: Hash of graph state

        Returns:
            Cache key string
        """
        return f"narrative:{session_id}:{focal_entity_id}:{graph_hash}"

    def calculate_graph_hash(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph
    ) -> str:
        """
        Calculate hash of graph state for constellation.

        Hash includes:
        - Entity verification tiers
        - Constellation membership
        - Relation count and types

        Args:
            constellation: Set of entity IDs
            graph: Knowledge graph

        Returns:
            Hash string
        """
        hash_components = []

        # Sort entities for consistent hashing
        sorted_entities = sorted(constellation)

        for entity_id in sorted_entities:
            entity = graph.get_entity(entity_id)
            if entity:
                # Include verification tier (changes when analyst verifies)
                verification = entity.get("verification", {})
                tier = verification.get("tier", "UNKNOWN")
                confidence = verification.get("confidence", 0.0)

                hash_components.append(f"{entity_id}:{tier}:{confidence:.2f}")

        # Include relation count
        relation_count = 0
        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")
            relation_count += len(relations)

        hash_components.append(f"relations:{relation_count}")

        # Calculate hash
        hash_input = "|".join(hash_components)
        graph_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return graph_hash

    def get(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached narrative.

        Args:
            session_id: User session ID
            focal_entity_id: Narrative focal point
            graph_hash: Hash of graph state

        Returns:
            Cached data dict or None if cache miss
        """
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)

        try:
            cached = self.client.get(key)
            if cached:
                logger.info(f"Cache hit: {key}")
                return json.loads(cached)
            else:
                logger.info(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None

    def set(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store narrative in cache.

        Args:
            session_id: User session ID
            focal_entity_id: Narrative focal point
            graph_hash: Hash of graph state
            data: Narrative data to cache
            ttl: Time to live in seconds (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
        ttl = ttl or self.default_ttl

        try:
            self.client.setex(
                name=key,
                time=ttl,
                value=json.dumps(data)
            )
            logger.info(f"Cached narrative: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False

    def invalidate_session(self, session_id: str) -> int:
        """
        Invalidate all cached narratives for a session.

        Args:
            session_id: Session to invalidate

        Returns:
            Number of keys deleted
        """
        pattern = f"narrative:{session_id}:*"
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cached narratives for session {session_id}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/narrative/test_cache.py -v`
Expected: PASS (5 tests)

**Step 6: Add graph hash test**

Add to `tests/narrative/test_cache.py`:

```python
def test_graph_hash_changes_on_verification_tier_change():
    """Test graph hash changes when entity verification tier changes."""
    from farmer_factory.structure.graph import KnowledgeGraph
    from farmer_factory.structure.schema import (
        Property,
        EntityType,
        VerificationTier,
        Verification
    )

    cache = NarrativeCache()

    # Create graph with TIER_3_AI entity
    kg = KnowledgeGraph(case_id="test_001")
    prop = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.75),
        extracted_from="doc_001"
    )
    kg.add_entity(prop)

    constellation = {"prop_001"}
    hash1 = cache.calculate_graph_hash(constellation, kg)

    # Update to TIER_2_ANALYST
    prop.verification.tier = VerificationTier.TIER_2_ANALYST
    prop.verification.confidence = 0.92
    kg.add_entity(prop)  # Update in graph

    hash2 = cache.calculate_graph_hash(constellation, kg)

    # Hashes should differ (cache invalidated)
    assert hash1 != hash2
```

**Step 7: Run tests**

Run: `pytest tests/narrative/test_cache.py -v`
Expected: PASS (6 tests)

**Step 8: Commit**

```bash
git add farmer_factory/narrative/cache.py tests/narrative/test_cache.py farmer_factory/requirements.txt
git commit -m "feat(narrative): implement session cache with graph-state invalidation"
```

---

## Task 7: Narrative Generator (Orchestrator)

**Files:**
- Create: `farmer_factory/narrative/generator.py`
- Create: `tests/narrative/test_generator.py`

**Step 1: Write failing test for generator**

Create `tests/narrative/test_generator.py`:

```python
"""Tests for narrative generator orchestrator."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Property,
    Person,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def sample_graph():
    """Create sample graph for testing."""
    kg = KnowledgeGraph(case_id="test_001")

    prop = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.92),
        extracted_from="doc_001,doc_003"
    )
    kg.add_entity(prop)

    person = Person(
        id="person_001",
        name="Mario Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.89),
        extracted_from="doc_001"
    )
    kg.add_entity(person)

    rel = Relation(
        id="rel_001",
        type=RelationType.OWNS,
        source_id="person_001",
        target_id="prop_001",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.90),
        extracted_from="doc_001"
    )
    kg.add_relation(rel)

    return kg


def test_generator_initialization():
    """Test NarrativeGenerator initialization."""
    generator = NarrativeGenerator(api_key="test_key")
    assert generator is not None


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_generate_narrative(mock_api_client, sample_graph):
    """Test full narrative generation pipeline."""
    # Mock API responses
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Stage 1: Fact extraction
    mock_client_instance.call_with_retry.side_effect = [
        # First call: fact extraction
        json.dumps([
            {
                "claim_text": "Mario Ceresa owned Villa Aurelia",
                "doc_id": "doc_001",
                "page": 2,
                "quote": "Mario Ceresa, propietario",
                "temporal_context": "1952",
                "fact_type": "OWNERSHIP"
            }
        ]),
        # Second call: narrative synthesis
        "Villa Aurelia was owned by Mario Ceresa in 1952 [①]."
    ]

    generator = NarrativeGenerator(api_key="test_key")

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    assert result is not None
    assert result.focal_entity_id is not None
    assert result.main_narrative != ""
    assert len(result.facts) > 0


def test_insufficient_data_returns_simple_narrative(sample_graph):
    """Test that constellations with <3 entities return simple narrative."""
    generator = NarrativeGenerator(api_key="test_key")

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    # Should skip AI generation for simple case
    assert "Limited context" in result.main_narrative or result.skip_ai_generation
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_generator.py::test_generator_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.generator'"

**Step 3: Implement narrative generator**

Create `farmer_factory/narrative/generator.py`:

```python
"""Narrative generation orchestrator (two-stage LLM process)."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.narrative.prompts import NarrativePrompts
from farmer_factory.narrative.cache import NarrativeCache
from farmer_factory.narrative.models import (
    NarrativeResult,
    FactualClaim,
    EvidenceCitation,
    ConflictingClaim
)
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.structure.schema import VerificationTier

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """Orchestrates two-stage narrative generation with caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize narrative generator.

        Args:
            api_key: Anthropic API key
            use_cache: Enable session caching
        """
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self.analyzer = ConstellationAnalyzer()
        self.prompts = NarrativePrompts()
        self.cache = NarrativeCache() if use_cache else None

    def generate(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph,
        session_id: str,
        max_cost_per_session: float = 5.0
    ) -> NarrativeResult:
        """
        Generate contextual narrative for clicked entity.

        **Pipeline:**
        1. Extract constellation around clicked node
        2. Identify optimal narrative hub
        3. Check cache (session + graph hash)
        4. Select model based on complexity
        5. Stage 1: Extract structured facts from graph
        6. Stage 2: Synthesize chronological narrative
        7. Cache result

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph
            session_id: User session ID (for caching)
            max_cost_per_session: Max API cost per session

        Returns:
            NarrativeResult with narrative and metadata
        """
        logger.info(f"Generating narrative for {clicked_node_id}")

        # Step 1-2: Analyze constellation and identify hub
        constellation, hub_id = self.analyzer.analyze(clicked_node_id, graph)

        if not hub_id:
            logger.warning("No hub identified, constellation empty")
            return self._create_error_result("Entity not found")

        # Handle insufficient data (< 3 entities)
        if len(constellation) < 3:
            return self._create_simple_narrative(hub_id, graph, len(constellation))

        # Step 3: Check cache
        if self.cache:
            graph_hash = self.cache.calculate_graph_hash(constellation, graph)
            cached = self.cache.get(session_id, hub_id, graph_hash)
            if cached:
                logger.info("Returning cached narrative")
                return NarrativeResult(**cached)

        # Step 4: Select model
        model = self.analyzer.select_model(constellation, graph)

        # Step 5: Extract facts
        hub_entity = graph.get_entity(hub_id)
        facts = self._extract_facts(
            focal_entity_id=hub_id,
            focal_entity_name=hub_entity.get("name", "Unknown"),
            focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
            constellation=constellation,
            graph=graph,
            model=model
        )

        # Step 6: Synthesize narrative
        narrative_text = self._synthesize_narrative(
            focal_entity_name=hub_entity.get("name", "Unknown"),
            facts=facts,
            model=model
        )

        # Build result
        result = self._build_result(
            focal_entity_id=hub_id,
            focal_entity_name=hub_entity.get("name", "Unknown"),
            focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
            constellation_size=len(constellation),
            model=model,
            narrative_text=narrative_text,
            facts=facts,
            graph=graph,
            constellation=constellation
        )

        # Step 7: Cache result
        if self.cache:
            self.cache.set(
                session_id=session_id,
                focal_entity_id=hub_id,
                graph_hash=graph_hash,
                data=result.model_dump()
            )

        return result

    def _extract_facts(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation: set,
        graph: KnowledgeGraph,
        model: str
    ) -> list:
        """
        Stage 1: Extract structured facts from graph.

        Uses LLM to parse graph into factual claims with evidence.
        """
        # Build graph context
        entities = []
        relations = []
        documents = set()

        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                entities.append(entity.get("name", entity_id))
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    documents.update(extracted_from.split(","))

            rels = graph.get_relations(entity_id, direction="both")
            for rel in rels:
                relations.append(rel.get("relation_type", "UNKNOWN"))

        graph_context = {
            "entities": list(set(entities)),
            "relations": list(set(relations)),
            "documents": list(documents)
        }

        # Build prompt
        prompt = self.prompts.build_fact_extraction_prompt(
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            graph_context=graph_context
        )

        # Call LLM
        model_name = "claude-3-haiku-20240307" if model == "haiku" else "claude-3-5-sonnet-20241022"
        response = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name,
            max_tokens=2000
        )

        # Parse response
        try:
            facts = json.loads(response)
            logger.info(f"Extracted {len(facts)} facts")
            return facts
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse fact extraction response: {e}")
            return []

    def _synthesize_narrative(
        self,
        focal_entity_name: str,
        facts: list,
        model: str
    ) -> str:
        """
        Stage 2: Synthesize chronological narrative from facts.

        Uses LLM to write narrative with inline citations.
        """
        if not facts:
            return f"{focal_entity_name} appears in documents with limited context."

        # Build prompt
        prompt = self.prompts.build_narrative_synthesis_prompt(
            focal_entity_name=focal_entity_name,
            facts=facts
        )

        # Call LLM
        model_name = "claude-3-haiku-20240307" if model == "haiku" else "claude-3-5-sonnet-20241022"
        narrative = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name,
            max_tokens=1500
        )

        return narrative

    def _build_result(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation_size: int,
        model: str,
        narrative_text: str,
        facts: list,
        graph: KnowledgeGraph,
        constellation: set
    ) -> NarrativeResult:
        """Build NarrativeResult from generation outputs."""
        # Convert facts to FactualClaim objects
        factual_claims = []
        for i, fact in enumerate(facts, 1):
            evidence = [
                EvidenceCitation(
                    doc_id=fact.get("doc_id", "unknown"),
                    page=fact.get("page"),
                    quote=fact.get("quote", ""),
                    confidence=0.85,  # TODO: Get from graph
                    verification_tier=VerificationTier.TIER_2_ANALYST
                )
            ]

            factual_claims.append(
                FactualClaim(
                    claim_text=fact.get("claim_text", ""),
                    citation_number=i,
                    evidence=evidence,
                    temporal_context=fact.get("temporal_context"),
                    fact_type=fact.get("fact_type")
                )
            )

        # Count unique documents
        unique_docs = set()
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    unique_docs.update(extracted_from.split(","))

        # Build confidence summary
        confidence_summary = {}
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                verification = entity.get("verification", {})
                tier = verification.get("tier", "UNKNOWN")
                confidence_summary[tier] = confidence_summary.get(tier, 0) + 1

        return NarrativeResult(
            focal_entity_id=focal_entity_id,
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            constellation_size=constellation_size,
            model_used=model,
            main_narrative=narrative_text,
            facts=factual_claims,
            conflicts=[],  # TODO: Implement conflict detection
            total_documents=len(unique_docs),
            total_citations=len(factual_claims),
            confidence_summary=confidence_summary
        )

    def _create_simple_narrative(
        self,
        entity_id: str,
        graph: KnowledgeGraph,
        entity_count: int
    ) -> NarrativeResult:
        """Create simple narrative for insufficient data (< 3 entities)."""
        entity = graph.get_entity(entity_id)
        if not entity:
            return self._create_error_result("Entity not found")

        name = entity.get("name", "Unknown")
        extracted_from = entity.get("extracted_from", "")
        doc_count = len(extracted_from.split(",")) if extracted_from else 0

        narrative = (
            f"{name} appears in {doc_count} document(s). "
            "Limited context for narrative."
        )

        return NarrativeResult(
            focal_entity_id=entity_id,
            focal_entity_name=name,
            focal_entity_type=entity.get("entity_type", "UNKNOWN"),
            constellation_size=entity_count,
            model_used="haiku",
            main_narrative=narrative,
            facts=[],
            total_documents=doc_count,
            total_citations=0,
            confidence_summary={}
        )

    def _create_error_result(self, error_message: str) -> NarrativeResult:
        """Create error result."""
        return NarrativeResult(
            focal_entity_id="error",
            focal_entity_name="Error",
            focal_entity_type="UNKNOWN",
            constellation_size=0,
            model_used="haiku",
            main_narrative=error_message,
            facts=[],
            total_documents=0,
            total_citations=0,
            confidence_summary={},
            quality_warning=error_message,
            show_warning_banner=True
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_generator.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add farmer_factory/narrative/generator.py tests/narrative/test_generator.py
git commit -m "feat(narrative): implement two-stage narrative generator orchestrator"
```

---

## Task 8: Integration Test with Real Graph

**Files:**
- Create: `tests/narrative/test_integration.py`

**Step 1: Write integration test**

Create `tests/narrative/test_integration.py`:

```python
"""Integration tests for narrative generation with real graph."""

import pytest
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Property,
    Person,
    Location,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def villa_aurelia_graph():
    """Create realistic Villa Aurelia graph."""
    kg = KnowledgeGraph(case_id="TEST-CERESA")

    # Villa Aurelia (hub)
    prop = Property(
        id="prop_villa_aurelia_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        property_type="Urban property",
        address="Calle 23, Vedado",
        area=500.0,
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.92
        ),
        extracted_from="doc_001,doc_003,doc_007,doc_012"
    )
    kg.add_entity(prop)

    # Location
    location = Location(
        id="loc_vedado_001",
        name="Vedado",
        entity_type=EntityType.LOCATION,
        location_type="Neighborhood",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.95
        ),
        extracted_from="doc_001"
    )
    kg.add_entity(location)

    # Mario Ceresa (original owner)
    mario = Person(
        id="person_mario_ceresa_001",
        name="Mario Ceresa",
        entity_type=EntityType.PERSON,
        profession="Businessman",
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.89
        ),
        extracted_from="doc_001,doc_003"
    )
    kg.add_entity(mario)

    # Juan Ceresa (heir)
    juan = Person(
        id="person_juan_ceresa_001",
        name="Juan Ceresa",
        entity_type=EntityType.PERSON,
        verification=Verification(
            tier=VerificationTier.TIER_2_ANALYST,
            confidence=0.87
        ),
        extracted_from="doc_007"
    )
    kg.add_entity(juan)

    # Relations
    rel1 = Relation(
        id="rel_001",
        type=RelationType.LOCATED_IN,
        source_id="prop_villa_aurelia_001",
        target_id="loc_vedado_001",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.90),
        extracted_from="doc_001"
    )
    kg.add_relation(rel1)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.OWNS,
        source_id="person_mario_ceresa_001",
        target_id="prop_villa_aurelia_001",
        date="1952",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.92),
        extracted_from="doc_001"
    )
    kg.add_relation(rel2)

    rel3 = Relation(
        id="rel_003",
        type=RelationType.SOLD,
        source_id="person_mario_ceresa_001",
        target_id="prop_villa_aurelia_001",
        date="1956",
        price=50000.0,
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.88),
        extracted_from="doc_007"
    )
    kg.add_relation(rel3)

    rel4 = Relation(
        id="rel_004",
        type=RelationType.OWNS,
        source_id="person_juan_ceresa_001",
        target_id="prop_villa_aurelia_001",
        date="1956",
        verification=Verification(tier=VerificationTier.TIER_2_ANALYST, confidence=0.85),
        extracted_from="doc_007"
    )
    kg.add_relation(rel4)

    return kg


@pytest.mark.integration
@pytest.mark.skipif(
    "not config.getoption('--run-integration')",
    reason="Integration test requires API key"
)
def test_villa_aurelia_narrative_generation(villa_aurelia_graph):
    """Test full narrative generation for Villa Aurelia."""
    generator = NarrativeGenerator(use_cache=False)

    result = generator.generate(
        clicked_node_id="person_mario_ceresa_001",
        graph=villa_aurelia_graph,
        session_id="test_session_001"
    )

    # Should identify property as hub
    assert result.focal_entity_id == "prop_villa_aurelia_001"
    assert result.focal_entity_name == "Villa Aurelia"

    # Should use Haiku (simple constellation)
    assert result.model_used == "haiku"

    # Should have narrative and facts
    assert len(result.main_narrative) > 0
    assert len(result.facts) > 0

    # Should have citations
    assert result.total_citations > 0
    assert result.total_documents > 0

    # Should have confidence summary
    assert "TIER_2_ANALYST" in result.confidence_summary


def test_hub_identification_prefers_property(villa_aurelia_graph):
    """Test that property is identified as hub over people."""
    from farmer_factory.narrative.constellation import ConstellationAnalyzer

    analyzer = ConstellationAnalyzer()

    # Click on Mario
    constellation, hub_id = analyzer.analyze(
        clicked_node_id="person_mario_ceresa_001",
        graph=villa_aurelia_graph
    )

    # Should identify Villa Aurelia as hub
    assert hub_id == "prop_villa_aurelia_001"


def test_model_selection_for_simple_constellation(villa_aurelia_graph):
    """Test that simple constellations use Haiku."""
    from farmer_factory.narrative.constellation import ConstellationAnalyzer

    analyzer = ConstellationAnalyzer()

    constellation, hub_id = analyzer.analyze(
        clicked_node_id="person_mario_ceresa_001",
        graph=villa_aurelia_graph
    )

    model = analyzer.select_model(constellation, villa_aurelia_graph)

    # 4 entities, 4 relations, 4 docs = complexity ~26 → Haiku
    assert model == "haiku"
```

**Step 2: Add pytest configuration for integration tests**

Add to `pytest.ini` (or create if doesn't exist):

```ini
[pytest]
markers =
    integration: marks tests as integration tests (deselect with '-m "not integration"')

addopts = --strict-markers
```

**Step 3: Run integration tests**

Run: `pytest tests/narrative/test_integration.py -v -m "not integration"`
Expected: PASS (2 tests skipped, 2 tests passed)

**Step 4: Commit**

```bash
git add tests/narrative/test_integration.py pytest.ini
git commit -m "test(narrative): add integration tests for full generation pipeline"
```

---

## Task 9: Update Module Exports

**Files:**
- Modify: `farmer_factory/narrative/__init__.py`

**Step 1: Write test for module exports**

Add to `tests/narrative/test_models.py`:

```python
def test_module_exports():
    """Test that narrative module exports all public classes."""
    from farmer_factory.narrative import (
        NarrativeGenerator,
        ConstellationAnalyzer,
        StoryScorer,
        NarrativeCache,
        NarrativePrompts,
        NarrativeResult,
        FactualClaim,
        EvidenceCitation,
        ConflictingClaim
    )

    assert NarrativeGenerator is not None
    assert ConstellationAnalyzer is not None
    assert StoryScorer is not None
    assert NarrativeCache is not None
    assert NarrativePrompts is not None
    assert NarrativeResult is not None
    assert FactualClaim is not None
    assert EvidenceCitation is not None
    assert ConflictingClaim is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_models.py::test_module_exports -v`
Expected: FAIL with "cannot import name 'NarrativeGenerator'"

**Step 3: Update module exports**

Modify `farmer_factory/narrative/__init__.py`:

```python
"""Contextual narrative generation module."""

from .models import (
    EvidenceCitation,
    ConflictingClaim,
    FactualClaim,
    NarrativeResult
)
from .scorer import StoryScorer
from .constellation import ConstellationAnalyzer
from .prompts import NarrativePrompts
from .cache import NarrativeCache
from .generator import NarrativeGenerator

__all__ = [
    # Models
    "EvidenceCitation",
    "ConflictingClaim",
    "FactualClaim",
    "NarrativeResult",
    # Services
    "StoryScorer",
    "ConstellationAnalyzer",
    "NarrativePrompts",
    "NarrativeCache",
    "NarrativeGenerator",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/narrative/test_models.py::test_module_exports -v`
Expected: PASS

**Step 5: Commit**

```bash
git add farmer_factory/narrative/__init__.py tests/narrative/test_models.py
git commit -m "feat(narrative): update module exports for all public classes"
```

---

## Task 10: Documentation

**Files:**
- Create: `farmer_factory/narrative/README.md`

**Step 1: Create module README**

Create `farmer_factory/narrative/README.md`:

```markdown
# Narrative Generation Module

Contextual narrative generation for knowledge graph entities with forensic intelligence narratives, inline citations, and conflict detection.

## Overview

This module provides user-driven narrative generation. When users click on any entity in the knowledge graph, the system:

1. Analyzes the connected component (constellation)
2. Identifies the optimal narrative focal point using story centrality scoring
3. Selects appropriate LLM model based on complexity
4. Generates a chronological narrative with inline citations
5. Caches the result with graph-state awareness

## Architecture

### Two-Stage Generation Process

**Stage 1: Fact Extraction**
- Parse graph into structured factual claims
- Each claim backed by document evidence
- Identify conflicts (competing claims)

**Stage 2: Narrative Synthesis**
- Write chronological story from verified facts
- Inline citations for every claim
- Present highest-confidence version, conflicts in sidebar

### Key Components

- **`generator.py`**: Orchestrator for two-stage narrative generation
- **`constellation.py`**: Graph analysis and hub identification
- **`scorer.py`**: Story centrality scoring algorithm
- **`prompts.py`**: LLM prompt templates
- **`cache.py`**: Session-scoped caching with graph-state invalidation
- **`models.py`**: Pydantic models for narrative output

## Usage

```python
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph

# Initialize generator
generator = NarrativeGenerator(api_key="your_api_key")

# Load graph
graph = KnowledgeGraph(case_id="TEST-CERESA")
# ... add entities and relations ...

# Generate narrative
result = generator.generate(
    clicked_node_id="person_mario_ceresa_001",
    graph=graph,
    session_id="user_session_123"
)

# Access narrative
print(result.main_narrative)
print(f"Model used: {result.model_used}")
print(f"Citations: {result.total_citations}")
```

## Story Centrality Scoring

Identifies optimal narrative focal points using weighted scoring:

**Type Weights** (properties are protagonists):
- PROPERTY: 10.0
- LOCATION: 8.0
- PERSON: 5.0
- ORGANIZATION: 3.0

**Scoring Formula:**
```
score = base_type_weight +
        (connection_count × 2.0) +
        (document_count × 3.0) +
        sum(relation_weights)
```

## Model Selection

**Complexity Score:**
```
complexity = (entities × 2) +
             (relations × 1.5) +
             (documents × 3)
```

- **complexity ≤ 50**: Use Haiku (cheap, fast)
- **complexity > 50**: Use Sonnet (deep analysis)

## Caching Strategy

Session-scoped caching with graph-state invalidation:

**Cache Key:**
```
narrative:{session_id}:{focal_entity_id}:{graph_hash}
```

**Graph Hash Includes:**
- Entity verification tiers
- Constellation membership
- Relation count

**Cache Invalidates When:**
- Analyst verifies entities (tier change)
- New entities added to constellation
- Relations modified

**TTL:** 1 hour (3600 seconds)

## Legal Compliance

All prompts constrain Claude to produce **Forensic Facts Only**:
- Only extract claims directly supported by documents
- Never infer or make legal conclusions
- Never assess ownership validity
- Use past tense, factual tone only
- Every claim must cite source document

## Testing

```bash
# Run unit tests
pytest tests/narrative/ -v

# Run integration tests (requires API key)
pytest tests/narrative/test_integration.py -v --run-integration

# Run specific test
pytest tests/narrative/test_scorer.py::test_property_scores_highest -v
```

## Example Output

**Main Narrative:**
```
Villa Aurelia first appears in records in 1952 when Mario Ceresa
acquired the property [①]. The property transferred to Juan Ceresa
in 1956 for 50,000 pesos [②]. In 1962, the property was confiscated
by the state with no record of compensation [③].
```

**Facts:**
```json
[
  {
    "claim_text": "Mario Ceresa owned Villa Aurelia in 1952",
    "citation_number": 1,
    "evidence": [
      {
        "doc_id": "doc_003",
        "page": 2,
        "quote": "Mario Ceresa, propietario de Villa Aurelia",
        "confidence": 0.92,
        "verification_tier": "TIER_2_ANALYST"
      }
    ],
    "temporal_context": "1952",
    "fact_type": "OWNERSHIP"
  }
]
```

## Cost Estimation

**Per-Entity Worst Case (TEST-CERESA):**
- Simple (≤3 connections): ~$0.0005 (Haiku)
- Complex (>3 connections): ~$0.009 (Sonnet)
- Cache hit: $0 (free)

**Session Limits:**
- Max $5 per session
- Cache hit rate target: >60%

## See Also

- **Design Doc**: `docs/plans/2026-01-25-narrative-generation-design.md`
- **Schema**: `farmer_factory/structure/SCHEMA.md`
- **Testing Guide**: `docs/architecture/TESTING.md`
```

**Step 2: Commit documentation**

```bash
git add farmer_factory/narrative/README.md
git commit -m "docs(narrative): add module README with usage and architecture"
```

---

## Execution Complete

Plan complete and saved to `docs/plans/2026-01-25-narrative-generation-implementation.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**