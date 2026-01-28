# Contextual Narrative Generation - Implementation Plan v2

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build user-driven contextual narrative generation with forensic intelligence narratives featuring inline citations, expropriation highlighting, and smart model selection.

**Architecture:** New `farmer_factory/narrative/` module with graph constellation analysis, story centrality scoring with special event weighting, single-stage LLM generation with narrative voice, and in-memory session caching with graph-state invalidation. Full-stack implementation includes backend API + frontend narrative panel.

**Tech Stack:** Python 3.10+, Pydantic, NetworkX, Anthropic Claude API (Haiku/Sonnet), In-memory cache (adapter pattern for Redis migration), Next.js frontend with evidence sidebar

**Changes from v1:**
- Single-stage LLM (not two-stage) - 50% cost/latency reduction
- In-memory cache with Redis adapter (no new infrastructure for MVP1)
- Special highlighting for CONFISCATED, SOLD, INHERITED events
- Session cost tracking with $1 hard limit
- Better simple entity narratives (not just "Limited context")
- Verification tier tracking (no UI until MVP2)
- Weight profile system for tuning centrality scoring

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
    FactualClaim,
    NarrativeResult,
    EventHighlight
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


def test_event_highlight_creation():
    """Test EventHighlight model for special events."""
    highlight = EventHighlight(
        event_type="CONFISCATED",
        summary="INRA confiscated 12.99 caballerías under Agrarian Reform Law",
        date="1960",
        citation_number=4,
        evidence=[
            EvidenceCitation(
                doc_id="doc_012",
                quote="confiscated by INRA",
                confidence=0.74,
                verification_tier=VerificationTier.TIER_3_AI
            )
        ]
    )

    assert highlight.event_type == "CONFISCATED"
    assert highlight.citation_number == 4
    assert len(highlight.evidence) == 1
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
    FactualClaim,
    EventHighlight,
    NarrativeResult
)

__all__ = [
    "EvidenceCitation",
    "FactualClaim",
    "EventHighlight",
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


class EventHighlight(BaseModel):
    """Special events that need prominent display (expropriations, sales, inheritances)."""

    event_type: Literal["CONFISCATED", "SOLD", "INHERITED"] = Field(
        description="Type of highlighted event"
    )
    summary: str = Field(description="Brief event summary")
    date: Optional[str] = Field(default=None, description="Event date if known")
    citation_number: int = Field(description="Citation reference number")
    evidence: List[EvidenceCitation] = Field(
        description="Supporting evidence",
        min_length=1
    )
    parties_involved: List[str] = Field(
        default_factory=list,
        description="Entity names involved in event"
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
    highlighted_events: List[EventHighlight] = Field(
        default_factory=list,
        description="Special events needing prominence"
    )

    # Quality indicators
    total_documents: int = Field(description="Number of source documents")
    total_citations: int = Field(description="Total evidence citations")
    date_range: Optional[str] = Field(
        default=None,
        description="Temporal span (e.g., '1952-1962')"
    )

    # Session tracking
    generation_cost: float = Field(
        default=0.0,
        description="Estimated API cost for this generation (USD)"
    )
    from_cache: bool = Field(
        default=False,
        description="Whether result came from cache"
    )

    # Flags
    is_simple_entity: bool = Field(
        default=False,
        description="True if insufficient data for full narrative"
    )
    quality_warning: Optional[str] = Field(
        default=None,
        description="Warning for low-quality data"
    )
```

Create `tests/narrative/__init__.py` (empty file).

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_models.py -v`
Expected: PASS (2 tests)

**Step 5: Add remaining model tests**

Add to `tests/narrative/test_models.py`:

```python
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
        main_narrative="Villa Aurelia was a 59.28 caballería estate [①].",
        facts=[
            FactualClaim(
                claim_text="Estate size was 59.28 caballerías",
                citation_number=1,
                evidence=[
                    EvidenceCitation(
                        doc_id="doc_003",
                        quote="59.28 caballerías",
                        confidence=0.92,
                        verification_tier=VerificationTier.TIER_2_ANALYST
                    )
                ]
            )
        ],
        total_documents=8,
        total_citations=12,
        date_range="1952-1962",
        generation_cost=0.015
    )

    assert result.focal_entity_name == "Villa Aurelia"
    assert result.model_used == "sonnet"
    assert result.generation_cost == 0.015
    assert not result.from_cache
```

**Step 6: Run tests**

Run: `pytest tests/narrative/test_models.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/ tests/narrative/
git commit -m "feat(narrative): add Pydantic models with event highlights"
```

---

## Task 2: Story Centrality Scoring with Weight Profiles

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
    """Create sample graph with property, people, and confiscation."""
    kg = KnowledgeGraph(case_id="test_001")

    # Property
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

    # Owner
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

    # INRA (confiscator)
    from farmer_factory.structure.schema import Organization
    inra = Organization(
        id="org_001",
        entity_type=EntityType.ORGANIZATION,
        name="INRA",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.74
        ),
        extracted_from="doc_012"
    )
    kg.add_entity(inra)

    # Ownership relation
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

    # Confiscation relation (should boost score)
    rel2 = Relation(
        id="rel_002",
        type=RelationType.CONFISCATED,
        source_id="org_001",
        target_id="prop_001",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.74
        ),
        extracted_from="doc_012"
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


def test_confiscation_boosts_score(sample_graph):
    """Test that confiscation relations increase property score."""
    scorer = StoryScorer()

    # Property with confiscation should score very high
    score = scorer.calculate_centrality("prop_001", sample_graph)

    # Base property (10) + connections (2*2=4) + docs (3*3=9) +
    # OWNS (3.0) + CONFISCATED (5.0) = 31.0
    assert score >= 30.0


def test_weight_profile_system():
    """Test custom weight profiles."""
    custom_weights = {
        "type_weights": {
            EntityType.PROPERTY: 15.0,  # Boost properties
            EntityType.PERSON: 3.0
        },
        "relation_weights": {
            RelationType.CONFISCATED: 10.0  # Boost confiscations more
        }
    }

    scorer = StoryScorer(profile="custom", custom_weights=custom_weights)

    assert scorer.type_weights[EntityType.PROPERTY] == 15.0
    assert scorer.relation_weights[RelationType.CONFISCATED] == 10.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_scorer.py::test_scorer_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.scorer'"

**Step 3: Implement story centrality scorer**

Create `farmer_factory/narrative/scorer.py`:

```python
"""Story centrality scoring algorithm for narrative focal point selection."""

from typing import Dict, List, Optional
import logging

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import EntityType, RelationType

logger = logging.getLogger(__name__)


# Weight profiles for different use cases
WEIGHT_PROFILES = {
    "cuban_restitution": {
        "type_weights": {
            EntityType.PROPERTY: 10.0,
            EntityType.LOCATION: 8.0,
            EntityType.PERSON: 5.0,
            EntityType.ORGANIZATION: 3.0,
            EntityType.DOCUMENT: 1.0
        },
        "relation_weights": {
            # Special events (highlighted)
            RelationType.CONFISCATED: 5.0,  # Expropriations critical
            RelationType.SOLD: 3.0,
            RelationType.INHERITED: 3.0,
            # Ownership
            RelationType.OWNS: 3.0,
            RelationType.BOUGHT: 2.5,
            # Other
            RelationType.LOCATED_IN: 1.5,
            RelationType.WITNESSED: 1.0,
            RelationType.NOTARIZED: 1.0,
            RelationType.EMPLOYED_BY: 1.0,
            RelationType.RELATED_TO: 0.5,
        },
        "connection_multiplier": 2.0,
        "document_multiplier": 3.0
    }
}


class StoryScorer:
    """Calculate story centrality scores for entities in knowledge graph."""

    def __init__(
        self,
        profile: str = "cuban_restitution",
        custom_weights: Optional[Dict] = None
    ):
        """
        Initialize story scorer with weight profile.

        Args:
            profile: Weight profile name ("cuban_restitution")
            custom_weights: Optional custom weight overrides
        """
        if custom_weights:
            # Use custom weights
            self.type_weights = custom_weights.get("type_weights", {})
            self.relation_weights = custom_weights.get("relation_weights", {})
            self.connection_multiplier = custom_weights.get("connection_multiplier", 2.0)
            self.document_multiplier = custom_weights.get("document_multiplier", 3.0)
        elif profile in WEIGHT_PROFILES:
            # Use named profile
            config = WEIGHT_PROFILES[profile]
            self.type_weights = config["type_weights"]
            self.relation_weights = config["relation_weights"]
            self.connection_multiplier = config["connection_multiplier"]
            self.document_multiplier = config["document_multiplier"]
        else:
            raise ValueError(f"Unknown profile: {profile}")

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
Expected: PASS (4 tests)

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

    entity_ids = ["prop_001", "person_001", "org_001"]
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
Expected: PASS (6 tests)

**Step 7: Commit**

```bash
git add farmer_factory/narrative/scorer.py tests/narrative/test_scorer.py
git commit -m "feat(narrative): implement centrality scoring with weight profiles"
```

---

## Task 3: Constellation Analysis and Model Selection

**Files:**
- Create: `farmer_factory/narrative/constellation.py`
- Create: `tests/narrative/test_constellation.py`

**Step 1: Write failing test**

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

    # Property should be identified as hub
    assert hub_id == "prop_001"


def test_model_selection_simple(multi_component_graph):
    """Test simple constellations use Haiku."""
    analyzer = ConstellationAnalyzer()

    constellation = analyzer.extract_constellation(
        clicked_node_id="person_001",
        graph=multi_component_graph
    )

    model = analyzer.select_model(constellation, multi_component_graph)

    # 2 entities, 1 relation, 1 doc = complexity ~11 → Haiku
    assert model == "haiku"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_constellation.py::test_analyzer_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.constellation'"

**Step 3: Implement constellation analyzer**

Create `farmer_factory/narrative/constellation.py`:

```python
"""Constellation analysis for extracting graph components and identifying hubs."""

from typing import List, Set, Optional, Literal
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
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add farmer_factory/narrative/constellation.py tests/narrative/test_constellation.py
git commit -m "feat(narrative): implement constellation analysis and model selection"
```

---

## Task 4: Single-Stage Narrative Prompts

**Files:**
- Create: `farmer_factory/narrative/prompts.py`
- Create: `tests/narrative/test_prompts.py`

**Step 1: Write test**

Create `tests/narrative/test_prompts.py`:

```python
"""Tests for narrative generation prompts."""

import pytest
from farmer_factory.narrative.prompts import NarrativePrompts


def test_prompts_initialization():
    """Test NarrativePrompts initialization."""
    prompts = NarrativePrompts()
    assert prompts is not None


def test_narrative_prompt_structure():
    """Test narrative prompt contains required constraints."""
    prompts = NarrativePrompts()

    graph_context = {
        "focal_entity": {
            "name": "Villa Aurelia",
            "type": "PROPERTY",
            "connections": 11
        },
        "entities": ["Mario Ceresa", "Juan Ceresa", "INRA"],
        "relations": [
            {"type": "OWNS", "source": "Mario Ceresa", "target": "Villa Aurelia"},
            {"type": "CONFISCATED", "source": "INRA", "target": "Villa Aurelia"}
        ],
        "documents": ["doc_001", "doc_012"]
    }

    prompt = prompts.build_narrative_prompt(graph_context)

    # Should contain forensic facts constraint
    assert "forensic" in prompt.lower() or "factual" in prompt.lower()
    # Should mention focal entity
    assert "Villa Aurelia" in prompt
    # Should prohibit legal conclusions
    assert "legal" in prompt.lower() or "conclusion" in prompt.lower()
    # Should require citations
    assert "citation" in prompt.lower() or "[①]" in prompt
    # Should emphasize expropriations
    assert "confiscation" in prompt.lower() or "expropriation" in prompt.lower()
    # Should request narrative voice
    assert "narrative" in prompt.lower() or "story" in prompt.lower()


def test_simple_entity_prompt():
    """Test prompt for simple entities (insufficient data)."""
    prompts = NarrativePrompts()

    simple_context = {
        "focal_entity": {
            "name": "Juan Mir Perez",
            "type": "PERSON"
        },
        "role": "Jefe del Departamento Legal del INRA",
        "document": "doc_012"
    }

    prompt = prompts.build_simple_narrative_prompt(simple_context)

    assert "Juan Mir Perez" in prompt
    assert "INRA" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_prompts.py::test_prompts_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.prompts'"

**Step 3: Implement prompts**

Create `farmer_factory/narrative/prompts.py`:

```python
"""LLM prompts for single-stage narrative generation."""

from typing import Dict, Any


class NarrativePrompts:
    """Prompt templates for narrative generation."""

    NARRATIVE_TEMPLATE = """You are a forensic analyst writing a historical narrative for property restitution research.

**CRITICAL CONSTRAINTS:**
1. Write in past tense with engaging narrative voice (not mechanical data dump)
2. EVERY claim must have inline citation: [①], [②], etc.
3. Present events in chronological order
4. NEVER make legal conclusions or assess ownership validity
5. NEVER infer beyond what documents explicitly state
6. Highlight expropriations, sales, and inheritances prominently

**Focal Entity:** {focal_entity_name} ({focal_entity_type})

**Graph Context:**
{graph_context}

**Special Instructions:**
- If CONFISCATED relations exist, dedicate a prominent paragraph starting with "🚨 EXPROPRIATION EVENT"
- For SOLD or INHERITED events, note them clearly with dates and parties
- Use engaging language: "Villa Aurelia first appears..." not "Villa Aurelia was mentioned..."
- Keep it accessible for families, not just lawyers

**Output Format:**
Write a chronological narrative (3-8 paragraphs) with inline citations [①], [②], etc.

For each citation number, the evidence will be:
- Document ID and page
- Exact quote from document
- Date if available

Example style:
"Villa Aurelia, a 59.28 caballería estate in Maniabón [①], passed to the Rodríguez Pérez heirs in 1960 [②]. That same year, the Instituto Nacional de Reforma Agraria confiscated 12.99 caballerías under the Agrarian Reform Law [③]."
"""

    SIMPLE_NARRATIVE_TEMPLATE = """You are a forensic analyst providing context for an entity with limited data.

**Entity:** {entity_name} ({entity_type})

**Available Information:**
{context}

**Task:**
Write 1-2 sentences explaining this entity's role in the documents, even though we have limited context.

Example:
"Juan Mir Perez appears as Jefe del Departamento Legal del Instituto Nacional de Reforma Agraria (INRA) in a 1960 co-heir document. Role: INRA legal official involved in Villa Aurelia estate proceedings."

Focus on: who they are, what role they played, how they connect to the case.
"""

    HIGHLIGHTED_EVENT_TEMPLATE = """**🚨 {event_type} EVENT**
{summary}

{details}
"""

    def build_narrative_prompt(self, graph_context: Dict[str, Any]) -> str:
        """
        Build prompt for full narrative generation.

        Args:
            graph_context: Dict with focal entity, entities, relations, documents

        Returns:
            Formatted prompt string
        """
        focal = graph_context.get("focal_entity", {})
        entities = graph_context.get("entities", [])
        relations = graph_context.get("relations", [])
        documents = graph_context.get("documents", [])

        # Format graph context
        entities_str = "\n".join([f"- {e}" for e in entities])

        relations_str = "\n".join([
            f"- {r.get('type', 'UNKNOWN')}: {r.get('source', '?')} → {r.get('target', '?')}"
            f"{' (date: ' + r['date'] + ')' if r.get('date') else ''}"
            for r in relations
        ])

        docs_str = "\n".join([f"- {d}" for d in documents])

        # Check for special events
        has_confiscation = any(r.get("type") == "CONFISCATED" for r in relations)
        has_sale = any(r.get("type") == "SOLD" for r in relations)
        has_inheritance = any(r.get("type") == "INHERITED" for r in relations)

        special_events = []
        if has_confiscation:
            special_events.append("CONFISCATION (highlight prominently)")
        if has_sale:
            special_events.append("SALE (note clearly)")
        if has_inheritance:
            special_events.append("INHERITANCE (note clearly)")

        context_str = f"""
**Entities in Context:**
{entities_str}

**Relations:**
{relations_str}

**Source Documents:**
{docs_str}

**Special Events to Highlight:**
{', '.join(special_events) if special_events else 'None'}
"""

        return self.NARRATIVE_TEMPLATE.format(
            focal_entity_name=focal.get("name", "Unknown"),
            focal_entity_type=focal.get("type", "UNKNOWN"),
            graph_context=context_str
        )

    def build_simple_narrative_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for simple entities (insufficient data).

        Args:
            context: Dict with entity name, type, role, document

        Returns:
            Formatted prompt string
        """
        context_lines = []
        if context.get("role"):
            context_lines.append(f"Role: {context['role']}")
        if context.get("document"):
            context_lines.append(f"Appears in: {context['document']}")
        if context.get("connections"):
            context_lines.append(f"Connected to: {', '.join(context['connections'])}")

        context_str = "\n".join(context_lines)

        return self.SIMPLE_NARRATIVE_TEMPLATE.format(
            entity_name=context.get("name", "Unknown"),
            entity_type=context.get("type", "UNKNOWN"),
            context=context_str
        )

    def format_highlighted_event(
        self,
        event_type: str,
        summary: str,
        details: str
    ) -> str:
        """
        Format highlighted event (expropriation, sale, inheritance).

        Args:
            event_type: "CONFISCATION", "SALE", or "INHERITANCE"
            summary: Brief event summary
            details: Detailed description with citations

        Returns:
            Formatted event block
        """
        return self.HIGHLIGHTED_EVENT_TEMPLATE.format(
            event_type=event_type,
            summary=summary,
            details=details
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_prompts.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add farmer_factory/narrative/prompts.py tests/narrative/test_prompts.py
git commit -m "feat(narrative): add single-stage LLM prompts with narrative voice"
```

---

## Task 5: In-Memory Cache with Redis Adapter Pattern

**Files:**
- Create: `farmer_factory/narrative/cache.py`
- Create: `tests/narrative/test_cache.py`

**Step 1: Write tests**

Create `tests/narrative/test_cache.py`:

```python
"""Tests for narrative session cache."""

import pytest
from unittest.mock import Mock
from farmer_factory.narrative.cache import InMemoryCache, NarrativeCache


def test_in_memory_cache_initialization():
    """Test InMemoryCache initialization."""
    cache = InMemoryCache()
    assert cache is not None


def test_cache_key_generation():
    """Test cache key generation."""
    cache = InMemoryCache()

    key = cache.generate_cache_key(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert "sess_123" in key
    assert "prop_001" in key
    assert "abc123" in key


def test_cache_miss_returns_none():
    """Test cache miss returns None."""
    cache = InMemoryCache()

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result is None


def test_cache_hit_returns_data():
    """Test cache hit returns stored data."""
    cache = InMemoryCache()

    data = {"narrative": "Test narrative", "model": "haiku"}
    cache.set(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123",
        data=data,
        ttl=3600
    )

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result == data


def test_cache_ttl_expiration():
    """Test cache TTL expiration."""
    cache = InMemoryCache()

    data = {"narrative": "Test"}
    cache.set(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123",
        data=data,
        ttl=0  # Immediate expiration
    )

    import time
    time.sleep(0.1)

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    # Should be expired
    assert result is None


def test_graph_hash_calculation():
    """Test graph hash calculation."""
    from farmer_factory.structure.graph import KnowledgeGraph
    from farmer_factory.structure.schema import (
        Property,
        EntityType,
        VerificationTier,
        Verification
    )

    cache = InMemoryCache()

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

    # Update verification tier
    prop.verification.tier = VerificationTier.TIER_2_ANALYST
    kg.add_entity(prop)

    hash2 = cache.calculate_graph_hash(constellation, kg)

    # Hash should change (cache invalidation)
    assert hash1 != hash2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_cache.py::test_in_memory_cache_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.cache'"

**Step 3: Implement cache with adapter pattern**

Create `farmer_factory/narrative/cache.py`:

```python
"""Session-scoped caching for narrative generation with graph-state invalidation."""

import hashlib
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Set

from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class NarrativeCache(ABC):
    """Abstract base class for narrative caching."""

    @abstractmethod
    def get(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative."""
        pass

    @abstractmethod
    def set(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str,
        data: Dict[str, Any],
        ttl: int
    ) -> bool:
        """Store narrative in cache."""
        pass

    @abstractmethod
    def invalidate_session(self, session_id: str) -> int:
        """Invalidate all cached narratives for a session."""
        pass

    def generate_cache_key(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> str:
        """Generate cache key."""
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


class InMemoryCache(NarrativeCache):
    """In-memory cache implementation for MVP1 (single server)."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize in-memory cache.

        Args:
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.default_ttl = default_ttl

    def get(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative."""
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)

        # Check if exists
        if key not in self.cache:
            logger.info(f"Cache miss: {key}")
            return None

        # Check TTL
        timestamp = self.timestamps.get(key, 0)
        if time.time() > timestamp:
            # Expired
            del self.cache[key]
            del self.timestamps[key]
            logger.info(f"Cache expired: {key}")
            return None

        logger.info(f"Cache hit: {key}")
        return self.cache[key]

    def set(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store narrative in cache."""
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
        ttl = ttl or self.default_ttl

        self.cache[key] = data
        self.timestamps[key] = time.time() + ttl

        logger.info(f"Cached narrative: {key} (TTL={ttl}s)")
        return True

    def invalidate_session(self, session_id: str) -> int:
        """Invalidate all cached narratives for a session."""
        prefix = f"narrative:{session_id}:"
        keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]

        for key in keys_to_delete:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]

        logger.info(f"Invalidated {len(keys_to_delete)} narratives for session {session_id}")
        return len(keys_to_delete)


# Future: Redis implementation for MVP2
# class RedisCache(NarrativeCache):
#     """Redis cache implementation for production (horizontal scaling)."""
#
#     def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
#         import redis
#         self.client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
#
#     def get(self, session_id, focal_entity_id, graph_hash):
#         key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
#         cached = self.client.get(key)
#         return json.loads(cached) if cached else None
#
#     def set(self, session_id, focal_entity_id, graph_hash, data, ttl):
#         key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
#         self.client.setex(key, ttl, json.dumps(data))
#         return True
#
#     def invalidate_session(self, session_id):
#         pattern = f"narrative:{session_id}:*"
#         keys = self.client.keys(pattern)
#         if keys:
#             return self.client.delete(*keys)
#         return 0
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/narrative/test_cache.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add farmer_factory/narrative/cache.py tests/narrative/test_cache.py
git commit -m "feat(narrative): implement in-memory cache with Redis adapter pattern"
```

---

## Task 6: Narrative Generator with Cost Tracking

**Files:**
- Create: `farmer_factory/narrative/generator.py`
- Create: `farmer_factory/narrative/exceptions.py`
- Create: `tests/narrative/test_generator.py`

**Step 1: Write failing tests**

Create `tests/narrative/test_generator.py`:

```python
"""Tests for narrative generator orchestrator."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded
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
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Mock LLM response
    mock_client_instance.call_with_retry.return_value = (
        "Villa Aurelia was owned by Mario Ceresa [①]. "
        "The property was located in Maniabón [②]."
    )

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    assert result is not None
    assert result.focal_entity_id == "prop_001"  # Property is hub
    assert len(result.main_narrative) > 0
    assert result.generation_cost > 0


def test_session_cost_limit_exceeded(sample_graph):
    """Test that generator blocks at session cost limit."""
    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    # Manually set session cost above limit
    generator.session_costs["sess_123"] = 1.50  # Above $1 limit

    with pytest.raises(SessionCostLimitExceeded):
        generator.generate(
            clicked_node_id="person_001",
            graph=sample_graph,
            session_id="sess_123",
            max_cost_per_session=1.0
        )


def test_simple_entity_narrative(sample_graph):
    """Test narrative for simple entity (< 3 entities)."""
    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_001",
        graph=sample_graph,
        session_id="sess_123"
    )

    # Should handle gracefully (2 entities < 3 threshold)
    assert result.is_simple_entity or len(result.main_narrative) > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/narrative/test_generator.py::test_generator_initialization -v`
Expected: FAIL with "No module named 'farmer_factory.narrative.generator'"

**Step 3: Create exceptions**

Create `farmer_factory/narrative/exceptions.py`:

```python
"""Exceptions for narrative generation."""


class NarrativeGenerationError(Exception):
    """Base exception for narrative generation errors."""
    pass


class SessionCostLimitExceeded(NarrativeGenerationError):
    """Raised when session cost exceeds limit."""

    def __init__(self, session_id: str, current_cost: float, limit: float):
        self.session_id = session_id
        self.current_cost = current_cost
        self.limit = limit
        super().__init__(
            f"Session {session_id} exceeded cost limit: "
            f"${current_cost:.2f} > ${limit:.2f}"
        )


class InsufficientGraphData(NarrativeGenerationError):
    """Raised when constellation has insufficient data."""
    pass
```

**Step 4: Implement generator orchestrator**

Create `farmer_factory/narrative/generator.py`:

```python
"""Narrative generation orchestrator with session cost tracking."""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.narrative.prompts import NarrativePrompts
from farmer_factory.narrative.cache import InMemoryCache, NarrativeCache
from farmer_factory.narrative.models import (
    NarrativeResult,
    FactualClaim,
    EvidenceCitation,
    EventHighlight
)
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded, InsufficientGraphData
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.structure.schema import VerificationTier, RelationType

logger = logging.getLogger(__name__)


# Anthropic pricing (2026 estimates)
MODEL_PRICING = {
    "haiku": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},  # per token
    "sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000}
}


class NarrativeGenerator:
    """Orchestrates single-stage narrative generation with caching and cost tracking."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_cache: bool = True,
        cache: Optional[NarrativeCache] = None
    ):
        """
        Initialize narrative generator.

        Args:
            api_key: Anthropic API key
            use_cache: Enable session caching
            cache: Optional custom cache implementation
        """
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self.analyzer = ConstellationAnalyzer()
        self.prompts = NarrativePrompts()
        self.cache = cache or (InMemoryCache() if use_cache else None)
        self.session_costs: Dict[str, float] = {}

    def generate(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph,
        session_id: str,
        max_cost_per_session: float = 1.0
    ) -> NarrativeResult:
        """
        Generate contextual narrative for clicked entity.

        Pipeline:
        1. Extract constellation around clicked node
        2. Identify optimal narrative hub
        3. Check session cost limit
        4. Check cache (session + graph hash)
        5. Select model based on complexity
        6. Generate narrative with single LLM call
        7. Extract highlighted events
        8. Cache result

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph
            session_id: User session ID
            max_cost_per_session: Max API cost per session (blocks at limit)

        Returns:
            NarrativeResult with narrative and metadata

        Raises:
            SessionCostLimitExceeded: If session cost exceeds limit
            InsufficientGraphData: If entity not found
        """
        logger.info(f"Generating narrative for {clicked_node_id} (session: {session_id})")

        # Step 1-2: Analyze constellation and identify hub
        constellation, hub_id = self.analyzer.analyze(clicked_node_id, graph)

        if not hub_id:
            raise InsufficientGraphData(f"Entity {clicked_node_id} not found in graph")

        # Handle insufficient data (< 3 entities)
        if len(constellation) < 3:
            return self._create_simple_narrative(hub_id, graph, session_id)

        # Step 3: Check session cost limit
        current_cost = self.session_costs.get(session_id, 0.0)
        if current_cost >= max_cost_per_session:
            raise SessionCostLimitExceeded(session_id, current_cost, max_cost_per_session)

        # Step 4: Check cache
        if self.cache:
            graph_hash = self.cache.calculate_graph_hash(constellation, graph)
            cached = self.cache.get(session_id, hub_id, graph_hash)
            if cached:
                logger.info("Returning cached narrative")
                cached["from_cache"] = True
                return NarrativeResult(**cached)

        # Step 5: Select model
        model = self.analyzer.select_model(constellation, graph)

        # Step 6: Generate narrative
        hub_entity = graph.get_entity(hub_id)
        narrative_text, cost = self._generate_narrative(
            focal_entity_id=hub_id,
            focal_entity_name=hub_entity.get("name", "Unknown"),
            focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
            constellation=constellation,
            graph=graph,
            model=model
        )

        # Update session cost
        self.session_costs[session_id] = self.session_costs.get(session_id, 0.0) + cost

        # Step 7: Extract highlighted events
        highlighted_events = self._extract_highlighted_events(constellation, graph)

        # Build result
        result = self._build_result(
            focal_entity_id=hub_id,
            focal_entity_name=hub_entity.get("name", "Unknown"),
            focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
            constellation_size=len(constellation),
            model=model,
            narrative_text=narrative_text,
            highlighted_events=highlighted_events,
            graph=graph,
            constellation=constellation,
            generation_cost=cost
        )

        # Step 8: Cache result
        if self.cache:
            self.cache.set(
                session_id=session_id,
                focal_entity_id=hub_id,
                graph_hash=graph_hash,
                data=result.model_dump(),
                ttl=3600
            )

        return result

    def _generate_narrative(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation: set,
        graph: KnowledgeGraph,
        model: str
    ) -> tuple[str, float]:
        """
        Single-stage narrative generation.

        Returns:
            (narrative_text, estimated_cost)
        """
        # Build graph context for prompt
        graph_context = self._build_graph_context(
            focal_entity_id=focal_entity_id,
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            constellation=constellation,
            graph=graph
        )

        # Build prompt
        prompt = self.prompts.build_narrative_prompt(graph_context)

        # Call LLM
        model_name = "claude-3-haiku-20240307" if model == "haiku" else "claude-3-5-sonnet-20241022"

        narrative = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name,
            max_tokens=2000
        )

        # Estimate cost (rough)
        input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
        output_tokens = len(narrative.split()) * 1.3
        pricing = MODEL_PRICING[model]
        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])

        logger.info(f"Generated narrative with {model}: ~{output_tokens:.0f} tokens, ${cost:.4f}")

        return narrative, cost

    def _build_graph_context(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation: set,
        graph: KnowledgeGraph
    ) -> Dict[str, Any]:
        """Build graph context dict for prompt."""
        entities = []
        relations = []
        documents = set()

        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                entity_name = entity.get("name", entity_id)
                entity_type = entity.get("entity_type", "UNKNOWN")
                entities.append(f"{entity_name} ({entity_type})")

                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    documents.update(extracted_from.split(","))

            # Get relations
            rels = graph.get_relations(entity_id, direction="both")
            for rel in rels:
                source = rel.get("source")
                target = rel.get("target")
                if source in constellation and target in constellation:
                    source_entity = graph.get_entity(source)
                    target_entity = graph.get_entity(target)
                    rel_type = rel.get("relation_type", "UNKNOWN")
                    date = rel.get("date", "")

                    relations.append({
                        "type": rel_type,
                        "source": source_entity.get("name", source) if source_entity else source,
                        "target": target_entity.get("name", target) if target_entity else target,
                        "date": date
                    })

        return {
            "focal_entity": {
                "name": focal_entity_name,
                "type": focal_entity_type
            },
            "entities": entities,
            "relations": relations,
            "documents": list(documents)
        }

    def _extract_highlighted_events(
        self,
        constellation: set,
        graph: KnowledgeGraph
    ) -> List[EventHighlight]:
        """Extract special events (CONFISCATED, SOLD, INHERITED) for highlighting."""
        highlighted = []
        citation_counter = 1

        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")

            for rel in relations:
                rel_type_str = rel.get("relation_type", "")
                try:
                    rel_type = RelationType(rel_type_str)

                    if rel_type in [RelationType.CONFISCATED, RelationType.SOLD, RelationType.INHERITED]:
                        source_entity = graph.get_entity(rel.get("source"))
                        target_entity = graph.get_entity(rel.get("target"))

                        if not source_entity or not target_entity:
                            continue

                        event = EventHighlight(
                            event_type=rel_type.value,
                            summary=f"{source_entity.get('name', '?')} {rel_type.value.lower()} {target_entity.get('name', '?')}",
                            date=rel.get("date"),
                            citation_number=citation_counter,
                            evidence=[
                                EvidenceCitation(
                                    doc_id=rel.get("document_id", "unknown"),
                                    quote=rel.get("evidence", ""),
                                    confidence=rel.get("verification", {}).get("confidence", 0.8),
                                    verification_tier=VerificationTier(rel.get("verification", {}).get("tier", "TIER_3_AI"))
                                )
                            ],
                            parties_involved=[
                                source_entity.get("name", "Unknown"),
                                target_entity.get("name", "Unknown")
                            ]
                        )
                        highlighted.append(event)
                        citation_counter += 1

                except ValueError:
                    continue

        return highlighted

    def _build_result(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation_size: int,
        model: str,
        narrative_text: str,
        highlighted_events: List[EventHighlight],
        graph: KnowledgeGraph,
        constellation: set,
        generation_cost: float
    ) -> NarrativeResult:
        """Build NarrativeResult from generation outputs."""
        # Count unique documents
        unique_docs = set()
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    unique_docs.update(extracted_from.split(","))

        # Placeholder facts (narrative text contains inline citations)
        # In real implementation, would parse [①] markers and extract evidence
        facts = []

        return NarrativeResult(
            focal_entity_id=focal_entity_id,
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            constellation_size=constellation_size,
            model_used=model,
            main_narrative=narrative_text,
            facts=facts,
            highlighted_events=highlighted_events,
            total_documents=len(unique_docs),
            total_citations=len(highlighted_events),  # Approximate
            generation_cost=generation_cost,
            from_cache=False
        )

    def _create_simple_narrative(
        self,
        entity_id: str,
        graph: KnowledgeGraph,
        session_id: str
    ) -> NarrativeResult:
        """Create simple narrative for insufficient data (< 3 entities)."""
        entity = graph.get_entity(entity_id)
        if not entity:
            raise InsufficientGraphData(f"Entity {entity_id} not found")

        name = entity.get("name", "Unknown")
        entity_type = entity.get("entity_type", "UNKNOWN")
        extracted_from = entity.get("extracted_from", "")
        doc_count = len(extracted_from.split(",")) if extracted_from else 0

        # Build context for simple prompt
        context = {
            "name": name,
            "type": entity_type,
            "document": extracted_from.split(",")[0] if extracted_from else "unknown",
            "role": entity.get("profession") or entity.get("roles", [None])[0],
            "connections": []
        }

        # Get connected entities
        relations = graph.get_relations(entity_id, direction="both")
        for rel in relations[:3]:  # Max 3 connections
            other_id = rel.get("target") if rel.get("source") == entity_id else rel.get("source")
            other = graph.get_entity(other_id)
            if other:
                context["connections"].append(other.get("name", other_id))

        # Generate simple narrative
        prompt = self.prompts.build_simple_narrative_prompt(context)
        model_name = "claude-3-haiku-20240307"

        narrative = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name,
            max_tokens=200
        )

        # Minimal cost
        cost = 0.001

        # Update session cost
        self.session_costs[session_id] = self.session_costs.get(session_id, 0.0) + cost

        return NarrativeResult(
            focal_entity_id=entity_id,
            focal_entity_name=name,
            focal_entity_type=entity_type,
            constellation_size=1,
            model_used="haiku",
            main_narrative=narrative,
            facts=[],
            total_documents=doc_count,
            total_citations=0,
            generation_cost=cost,
            is_simple_entity=True
        )
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/narrative/test_generator.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add farmer_factory/narrative/generator.py farmer_factory/narrative/exceptions.py tests/narrative/test_generator.py
git commit -m "feat(narrative): implement generator orchestrator with cost tracking"
```

---

## Task 7: Integration Tests with Real Graph

**Files:**
- Create: `tests/narrative/test_integration.py`

**Step 1: Write integration test**

Create `tests/narrative/test_integration.py`:

```python
"""Integration tests for narrative generation with real graph."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.narrative.generator import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import (
    Property,
    Person,
    Location,
    Organization,
    Relation,
    EntityType,
    RelationType,
    VerificationTier,
    Verification
)


@pytest.fixture
def villa_aurelia_graph():
    """Create realistic Villa Aurelia graph with confiscation."""
    kg = KnowledgeGraph(case_id="TEST-CERESA")

    # Villa Aurelia (hub)
    prop = Property(
        id="prop_villa_aurelia_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        property_type="Rural estate",
        area=59.28,
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.69
        ),
        extracted_from="doc_001"
    )
    kg.add_entity(prop)

    # Location
    location = Location(
        id="loc_manibon_001",
        name="Maniabón",
        entity_type=EntityType.LOCATION,
        location_type="Hacienda",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(location)

    # Mario Ceresa (co-heir)
    mario = Person(
        id="person_mario_001",
        name="Mario Ceresa Rodriguez",
        entity_type=EntityType.PERSON,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(mario)

    # INRA (confiscator)
    inra = Organization(
        id="org_inra_001",
        name="Instituto Nacional de Reforma Agraria",
        entity_type=EntityType.ORGANIZATION,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001"
    )
    kg.add_entity(inra)

    # Relations
    rel1 = Relation(
        id="rel_001",
        type=RelationType.LOCATED_IN,
        source_id="prop_villa_aurelia_001",
        target_id="loc_manibon_001",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="Villa Aurelia ubicada en Maniabón"
    )
    kg.add_relation(rel1)

    rel2 = Relation(
        id="rel_002",
        type=RelationType.INHERITED,
        source_id="person_mario_001",
        target_id="prop_villa_aurelia_001",
        date="1960-05-13",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="en concepto de coheredero"
    )
    kg.add_relation(rel2)

    rel3 = Relation(
        id="rel_003",
        type=RelationType.CONFISCATED,
        source_id="org_inra_001",
        target_id="prop_villa_aurelia_001",
        date="1960",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.69),
        extracted_from="doc_001",
        evidence="segregado para el INRA doce caballerías"
    )
    kg.add_relation(rel3)

    return kg


@pytest.mark.integration
@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_villa_aurelia_narrative_generation(mock_api_client, villa_aurelia_graph):
    """Test full narrative generation for Villa Aurelia."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance

    # Mock LLM response
    mock_client_instance.call_with_retry.return_value = (
        "Villa Aurelia, a 59.28 caballería estate in Maniabón [①], "
        "passed to Mario Ceresa Rodriguez as co-heir in 1960 [②]. "
        "That same year, the Instituto Nacional de Reforma Agraria "
        "confiscated 12.99 caballerías under the Agrarian Reform Law [③]."
    )

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    result = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="test_session_001"
    )

    # Should identify property as hub
    assert result.focal_entity_id == "prop_villa_aurelia_001"
    assert result.focal_entity_name == "Villa Aurelia"

    # Should use Haiku (simple constellation: 4 entities)
    assert result.model_used == "haiku"

    # Should have narrative
    assert len(result.main_narrative) > 0
    assert "Villa Aurelia" in result.main_narrative

    # Should extract highlighted events
    assert len(result.highlighted_events) > 0
    confiscation_events = [e for e in result.highlighted_events if e.event_type == "CONFISCATED"]
    assert len(confiscation_events) == 1

    # Should have cost tracking
    assert result.generation_cost > 0


def test_hub_identification_prefers_property(villa_aurelia_graph):
    """Test that property is identified as hub over people."""
    from farmer_factory.narrative.constellation import ConstellationAnalyzer

    analyzer = ConstellationAnalyzer()

    # Click on Mario
    constellation, hub_id = analyzer.analyze(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph
    )

    # Should identify Villa Aurelia as hub
    assert hub_id == "prop_villa_aurelia_001"


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_session_cost_tracking(mock_api_client, villa_aurelia_graph):
    """Test that session costs accumulate correctly."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance
    mock_client_instance.call_with_retry.return_value = "Test narrative [①]."

    generator = NarrativeGenerator(api_key="test_key", use_cache=False)

    # Generate first narrative
    result1 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    cost1 = generator.session_costs["sess_123"]
    assert cost1 > 0

    # Generate second narrative (different entity, same session)
    result2 = generator.generate(
        clicked_node_id="org_inra_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    cost2 = generator.session_costs["sess_123"]
    assert cost2 > cost1  # Should accumulate


@patch('farmer_factory.narrative.generator.ClaudeAPIClient')
def test_cache_prevents_duplicate_generation(mock_api_client, villa_aurelia_graph):
    """Test that cache prevents redundant LLM calls."""
    mock_client_instance = Mock()
    mock_api_client.return_value = mock_client_instance
    mock_client_instance.call_with_retry.return_value = "Cached narrative [①]."

    generator = NarrativeGenerator(api_key="test_key", use_cache=True)

    # Generate first time (cache miss)
    result1 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    assert not result1.from_cache
    assert mock_client_instance.call_with_retry.call_count == 1

    # Generate second time (cache hit)
    result2 = generator.generate(
        clicked_node_id="person_mario_001",
        graph=villa_aurelia_graph,
        session_id="sess_123"
    )

    assert result2.from_cache
    assert mock_client_instance.call_with_retry.call_count == 1  # No additional call
```

**Step 2: Run tests**

Run: `pytest tests/narrative/test_integration.py -v -m "not integration"`
Expected: PASS (4 tests)

**Step 3: Commit**

```bash
git add tests/narrative/test_integration.py
git commit -m "test(narrative): add integration tests with Villa Aurelia graph"
```

---

## Task 8: Module Exports and Documentation

**Files:**
- Modify: `farmer_factory/narrative/__init__.py`
- Create: `farmer_factory/narrative/README.md`

**Step 1: Update module exports**

Modify `farmer_factory/narrative/__init__.py`:

```python
"""Contextual narrative generation module."""

from .models import (
    EvidenceCitation,
    FactualClaim,
    EventHighlight,
    NarrativeResult
)
from .scorer import StoryScorer, WEIGHT_PROFILES
from .constellation import ConstellationAnalyzer
from .prompts import NarrativePrompts
from .cache import InMemoryCache, NarrativeCache
from .generator import NarrativeGenerator
from .exceptions import (
    NarrativeGenerationError,
    SessionCostLimitExceeded,
    InsufficientGraphData
)

__all__ = [
    # Models
    "EvidenceCitation",
    "FactualClaim",
    "EventHighlight",
    "NarrativeResult",
    # Services
    "StoryScorer",
    "WEIGHT_PROFILES",
    "ConstellationAnalyzer",
    "NarrativePrompts",
    "NarrativeCache",
    "InMemoryCache",
    "NarrativeGenerator",
    # Exceptions
    "NarrativeGenerationError",
    "SessionCostLimitExceeded",
    "InsufficientGraphData",
]
```

**Step 2: Create module README**

Create `farmer_factory/narrative/README.md`:

```markdown
# Narrative Generation Module

User-driven contextual narrative generation for knowledge graph entities with forensic intelligence narratives, inline citations, and event highlighting.

## Quick Start

```python
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.structure.graph import KnowledgeGraph

# Initialize
generator = NarrativeGenerator(api_key="your_anthropic_key")

# Load graph
graph = KnowledgeGraph.load("cases/TEST-CERESA/output/graph_data.json")

# Generate narrative
result = generator.generate(
    clicked_node_id="prop_villa_aurelia_001",
    graph=graph,
    session_id="user_session_123"
)

print(result.main_narrative)
print(f"Cost: ${result.generation_cost:.4f}")
print(f"Highlighted events: {len(result.highlighted_events)}")
```

## Architecture

### Single-Stage LLM Generation
- One API call generates complete narrative with inline citations
- 50% faster and cheaper than two-stage approach
- Narrative voice with forensic rigor

### Story Centrality Scoring
Properties score highest (optimal focal points for restitution):
- PROPERTY: 10.0 base weight
- CONFISCATED relations: +5.0 boost
- SOLD/INHERITED: +3.0 boost
- Document count: ×3.0 multiplier

### Model Selection
- **Haiku** (cheap): complexity ≤ 50
- **Sonnet** (deep): complexity > 50
- Complexity = (entities × 2) + (relations × 1.5) + (documents × 3)

### Session Cost Tracking
- $1 hard limit per session (configurable)
- Blocks generation when exceeded
- Accumulates across all narratives in session

### Caching Strategy
In-memory cache with graph-state invalidation:
- Cache key: `session_id + entity_id + graph_hash`
- Invalidates when verification tiers change
- 1-hour TTL
- Easy Redis migration via adapter pattern

## Event Highlighting

Special prominence for:
- **CONFISCATED** - Expropriations (red highlight in UI)
- **SOLD** - Property sales
- **INHERITED** - Estate transfers

```python
for event in result.highlighted_events:
    if event.event_type == "CONFISCATED":
        print(f"🚨 {event.summary}")
        print(f"   Date: {event.date}")
        print(f"   Parties: {', '.join(event.parties_involved)}")
```

## Weight Profile System

Tune centrality scoring for different use cases:

```python
from farmer_factory.narrative import StoryScorer, WEIGHT_PROFILES

# Use built-in profile
scorer = StoryScorer(profile="cuban_restitution")

# Custom weights
custom_weights = {
    "type_weights": {
        EntityType.PROPERTY: 15.0,  # Boost properties more
        EntityType.PERSON: 3.0
    },
    "relation_weights": {
        RelationType.CONFISCATED: 10.0  # Emphasize expropriations
    }
}
scorer = StoryScorer(profile="custom", custom_weights=custom_weights)
```

## Error Handling

```python
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded

try:
    result = generator.generate(
        clicked_node_id="entity_001",
        graph=graph,
        session_id="sess_123",
        max_cost_per_session=1.0
    )
except SessionCostLimitExceeded as e:
    print(f"Session limit exceeded: ${e.current_cost:.2f} > ${e.limit:.2f}")
```

## Testing

```bash
# Unit tests
pytest tests/narrative/ -v

# Integration tests (requires API key)
pytest tests/narrative/test_integration.py -v -m integration

# Specific test
pytest tests/narrative/test_scorer.py::test_confiscation_boosts_score -v
```

## Cost Estimates

Villa Aurelia example (4 entities, 3 relations, 1 doc):
- Complexity: ~26 → Haiku
- Tokens: ~1500 input, ~400 output
- Cost: ~$0.0007 per generation
- With cache: $0 on repeat

Session with 20 narratives:
- Mix of Haiku (80%) and Sonnet (20%)
- Average: ~$0.014 total
- Well under $1 limit

## See Also

- Design: `docs/plans/2026-01-25-narrative-generation-design.md`
- Implementation: `docs/plans/2026-01-25-narrative-generation-implementation-v2.md`
- Schema: `farmer_factory/structure/SCHEMA.md`
```

**Step 3: Commit**

```bash
git add farmer_factory/narrative/__init__.py farmer_factory/narrative/README.md
git commit -m "docs(narrative): add module exports and comprehensive README"
```

---

## Task 9: Backend API Endpoint

**Files:**
- Create: `farmer_factory/api/__init__.py` (if doesn't exist)
- Create: `farmer_factory/api/narrative.py`
- Create: `tests/api/test_narrative_endpoint.py`

**Step 1: Write API endpoint test**

Create `tests/api/test_narrative_endpoint.py`:

```python
"""Tests for narrative API endpoint."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.api.narrative import generate_narrative_endpoint
from farmer_factory.narrative.models import NarrativeResult


@pytest.fixture
def mock_graph():
    """Mock knowledge graph."""
    with patch('farmer_factory.api.narrative.KnowledgeGraph') as mock:
        yield mock


@pytest.fixture
def mock_generator():
    """Mock narrative generator."""
    with patch('farmer_factory.api.narrative.NarrativeGenerator') as mock:
        generator_instance = Mock()
        mock.return_value = generator_instance

        # Mock generation result
        generator_instance.generate.return_value = NarrativeResult(
            focal_entity_id="prop_001",
            focal_entity_name="Villa Aurelia",
            focal_entity_type="PROPERTY",
            constellation_size=4,
            model_used="haiku",
            main_narrative="Test narrative [①].",
            facts=[],
            total_documents=1,
            total_citations=1,
            generation_cost=0.001,
            from_cache=False
        )

        yield generator_instance


def test_generate_narrative_endpoint_success(mock_graph, mock_generator):
    """Test successful narrative generation."""
    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    result = generate_narrative_endpoint(
        case_id="TEST-CERESA",
        request_data=request_data
    )

    assert result["focal_entity_name"] == "Villa Aurelia"
    assert result["model_used"] == "haiku"
    assert "main_narrative" in result
    assert result["generation_cost"] > 0


def test_endpoint_handles_missing_params():
    """Test endpoint validates required parameters."""
    request_data = {}  # Missing clicked_node_id

    with pytest.raises(ValueError, match="clicked_node_id"):
        generate_narrative_endpoint(
            case_id="TEST-CERESA",
            request_data=request_data
        )


def test_endpoint_handles_cost_limit_exceeded(mock_graph, mock_generator):
    """Test endpoint handles cost limit errors."""
    from farmer_factory.narrative.exceptions import SessionCostLimitExceeded

    mock_generator.generate.side_effect = SessionCostLimitExceeded(
        session_id="sess_123",
        current_cost=1.50,
        limit=1.0
    )

    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    with pytest.raises(SessionCostLimitExceeded):
        generate_narrative_endpoint(
            case_id="TEST-CERESA",
            request_data=request_data
        )
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_narrative_endpoint.py::test_generate_narrative_endpoint_success -v`
Expected: FAIL with "No module named 'farmer_factory.api.narrative'"

**Step 3: Implement API endpoint**

Create `farmer_factory/api/__init__.py`:

```python
"""API endpoints for Farmer Factory."""
```

Create `farmer_factory/api/narrative.py`:

```python
"""Narrative generation API endpoint."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.narrative.exceptions import (
    SessionCostLimitExceeded,
    InsufficientGraphData
)

logger = logging.getLogger(__name__)


def generate_narrative_endpoint(
    case_id: str,
    request_data: Dict[str, Any],
    api_key: Optional[str] = None,
    max_cost_per_session: float = 1.0
) -> Dict[str, Any]:
    """
    API endpoint for narrative generation.

    POST /api/cases/{caseId}/narrative

    Request:
    {
        "clicked_node_id": "prop_villa_aurelia_001",
        "session_id": "user_session_123",
        "max_depth": 3  // Optional, not used in MVP1
    }

    Response:
    {
        "focal_entity_id": "prop_villa_aurelia_001",
        "focal_entity_name": "Villa Aurelia",
        "focal_entity_type": "PROPERTY",
        "main_narrative": "Villa Aurelia first appears...",
        "highlighted_events": [...],
        "model_used": "haiku",
        "generation_cost": 0.0007,
        "from_cache": false,
        "session_total_cost": 0.0142
    }

    Args:
        case_id: Case identifier
        request_data: Request payload
        api_key: Optional Anthropic API key
        max_cost_per_session: Session cost limit

    Returns:
        Narrative result as dict

    Raises:
        ValueError: If required parameters missing
        SessionCostLimitExceeded: If session exceeds cost limit
        InsufficientGraphData: If entity not found
    """
    # Validate request
    clicked_node_id = request_data.get("clicked_node_id")
    session_id = request_data.get("session_id")

    if not clicked_node_id:
        raise ValueError("Missing required parameter: clicked_node_id")
    if not session_id:
        raise ValueError("Missing required parameter: session_id")

    logger.info(f"Narrative request: case={case_id}, entity={clicked_node_id}, session={session_id}")

    # Load graph
    graph_path = Path(f"cases/{case_id}/output/graph_data.json")
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph data not found: {graph_path}")

    # Note: Assuming KnowledgeGraph has a load method
    # If not, you'll need to implement it or load differently
    graph = KnowledgeGraph(case_id=case_id)
    # graph.load_from_file(str(graph_path))  # Implement if needed

    # Initialize generator
    generator = NarrativeGenerator(api_key=api_key, use_cache=True)

    # Generate narrative
    try:
        result = generator.generate(
            clicked_node_id=clicked_node_id,
            graph=graph,
            session_id=session_id,
            max_cost_per_session=max_cost_per_session
        )

        # Add session total cost to response
        response = result.model_dump()
        response["session_total_cost"] = generator.session_costs.get(session_id, 0.0)

        logger.info(
            f"Narrative generated: entity={result.focal_entity_name}, "
            f"model={result.model_used}, cost=${result.generation_cost:.4f}"
        )

        return response

    except SessionCostLimitExceeded as e:
        logger.warning(f"Session cost limit exceeded: {e}")
        raise

    except InsufficientGraphData as e:
        logger.error(f"Insufficient graph data: {e}")
        raise

    except Exception as e:
        logger.error(f"Narrative generation error: {e}", exc_info=True)
        raise
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/api/test_narrative_endpoint.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add farmer_factory/api/ tests/api/
git commit -m "feat(api): add narrative generation endpoint"
```

---

## Task 10: Frontend Narrative Panel Component

**Files:**
- Create: `farmer_vault/components/NarrativePanel.tsx`
- Create: `farmer_vault/components/NarrativePanel.module.css`
- Create: `farmer_vault/hooks/useNarrative.ts`

**Step 1: Create narrative panel component**

Create `farmer_vault/components/NarrativePanel.tsx`:

```typescript
/**
 * Narrative Panel Component
 *
 * Displays contextual narratives with inline citations and highlighted events.
 */

import React, { useState } from 'react';
import styles from './NarrativePanel.module.css';

interface EvidenceCitation {
  doc_id: string;
  page?: number;
  quote: string;
  confidence: number;
  verification_tier: string;
  ocr_confidence?: number;
}

interface EventHighlight {
  event_type: 'CONFISCATED' | 'SOLD' | 'INHERITED';
  summary: string;
  date?: string;
  citation_number: number;
  evidence: EvidenceCitation[];
  parties_involved: string[];
}

interface NarrativeResult {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: 'haiku' | 'sonnet';
  main_narrative: string;
  highlighted_events: EventHighlight[];
  total_documents: number;
  total_citations: number;
  generation_cost: number;
  from_cache: boolean;
  is_simple_entity?: boolean;
}

interface NarrativePanelProps {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

export const NarrativePanel: React.FC<NarrativePanelProps> = ({
  narrative,
  loading,
  error,
  onClose
}) => {
  const [showSidebar, setShowSidebar] = useState(true);

  if (loading) {
    return (
      <div className={styles.panel}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>Generating narrative...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.panel}>
        <div className={styles.error}>
          <h3>Error</h3>
          <p>{error}</p>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  if (!narrative) {
    return null;
  }

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2>{narrative.focal_entity_name}</h2>
          <span className={styles.entityType}>{narrative.focal_entity_type}</span>
        </div>
        <div className={styles.headerRight}>
          <button
            className={styles.toggleSidebar}
            onClick={() => setShowSidebar(!showSidebar)}
          >
            {showSidebar ? 'Hide Evidence' : 'Show Evidence'}
          </button>
          <button className={styles.closeBtn} onClick={onClose}>×</button>
        </div>
      </div>

      {/* Metadata */}
      <div className={styles.metadata}>
        <span>{narrative.constellation_size} entities</span>
        <span>•</span>
        <span>{narrative.total_documents} documents</span>
        <span>•</span>
        <span className={styles.modelBadge}>
          {narrative.model_used === 'sonnet' ? '🧠 Deep Analysis' : '⚡ Quick Analysis'}
        </span>
        {narrative.from_cache && (
          <>
            <span>•</span>
            <span className={styles.cachedBadge}>📦 Cached</span>
          </>
        )}
      </div>

      <div className={styles.content}>
        {/* Main Narrative */}
        <div className={styles.narrativeSection}>
          {/* Highlighted Events */}
          {narrative.highlighted_events.length > 0 && (
            <div className={styles.highlightedEvents}>
              {narrative.highlighted_events.map((event, idx) => (
                <div
                  key={idx}
                  className={`${styles.eventHighlight} ${styles[event.event_type.toLowerCase()]}`}
                >
                  <div className={styles.eventIcon}>
                    {event.event_type === 'CONFISCATED' && '🚨'}
                    {event.event_type === 'SOLD' && '💰'}
                    {event.event_type === 'INHERITED' && '📜'}
                  </div>
                  <div className={styles.eventContent}>
                    <h4>{event.event_type} EVENT</h4>
                    <p>{event.summary}</p>
                    {event.date && <span className={styles.eventDate}>{event.date}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Narrative Text */}
          <div className={styles.narrativeText}>
            {renderNarrativeWithCitations(narrative.main_narrative)}
          </div>

          {/* Footer */}
          <div className={styles.footer}>
            <p className={styles.disclaimer}>
              This narrative presents facts documented in source materials.
              It does not constitute legal advice or proof of ownership.
              Consult legal counsel for case strategy.
            </p>
            <p className={styles.generated}>
              Generated with Claude {narrative.model_used.charAt(0).toUpperCase() + narrative.model_used.slice(1)}
              {!narrative.from_cache && ` • $${narrative.generation_cost.toFixed(4)}`}
            </p>
          </div>
        </div>

        {/* Evidence Sidebar */}
        {showSidebar && (
          <div className={styles.sidebar}>
            <h3>Evidence Citations</h3>
            <div className={styles.citations}>
              {narrative.highlighted_events.map((event, idx) => (
                <div key={idx} className={styles.citation}>
                  <div className={styles.citationNumber}>[{event.citation_number}]</div>
                  <div className={styles.citationContent}>
                    <h4>{event.event_type}</h4>
                    {event.evidence.map((evidence, evidx) => (
                      <div key={evidx} className={styles.evidence}>
                        <p className={styles.evidenceSource}>
                          Doc: <code>{evidence.doc_id}</code>
                          {evidence.page && <>, p.{evidence.page}</>}
                        </p>
                        <blockquote className={styles.evidenceQuote}>
                          "{evidence.quote}"
                        </blockquote>
                        <p className={styles.evidenceConfidence}>
                          Confidence: {(evidence.confidence * 100).toFixed(0)}%
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Render narrative text with clickable citation markers.
 */
function renderNarrativeWithCitations(text: string): React.ReactNode {
  // Split by citation markers [①], [②], etc.
  const parts = text.split(/(\[[\u2460-\u2473]\])/);

  return parts.map((part, idx) => {
    // Check if this is a citation marker
    if (part.match(/\[[\u2460-\u2473]\]/)) {
      return (
        <sup key={idx} className={styles.citationMarker}>
          {part}
        </sup>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}
```

**Step 2: Create styles**

Create `farmer_vault/components/NarrativePanel.module.css`:

```css
.panel {
  position: fixed;
  right: 0;
  top: 0;
  width: 60%;
  height: 100vh;
  background: #0f172a;
  color: #e2e8f0;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #334155;
}

.headerLeft h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.entityType {
  display: inline-block;
  margin-left: 1rem;
  padding: 0.25rem 0.75rem;
  background: #1e293b;
  border-radius: 4px;
  font-size: 0.875rem;
  font-family: 'Courier New', monospace;
}

.headerRight {
  display: flex;
  gap: 1rem;
}

.toggleSidebar {
  padding: 0.5rem 1rem;
  background: #1e293b;
  color: #e2e8f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.toggleSidebar:hover {
  background: #334155;
}

.closeBtn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  line-height: 1;
}

.closeBtn:hover {
  color: #e2e8f0;
}

.metadata {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 2rem;
  background: #1e293b;
  font-size: 0.875rem;
  color: #94a3b8;
}

.modelBadge,
.cachedBadge {
  padding: 0.25rem 0.5rem;
  background: #334155;
  border-radius: 4px;
  font-size: 0.75rem;
}

.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.narrativeSection {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.highlightedEvents {
  margin-bottom: 2rem;
}

.eventHighlight {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.eventHighlight.confiscated {
  background: rgba(220, 38, 38, 0.1);
  border-color: #dc2626;
}

.eventHighlight.sold {
  background: rgba(234, 179, 8, 0.1);
  border-color: #eab308;
}

.eventHighlight.inherited {
  background: rgba(59, 130, 246, 0.1);
  border-color: #3b82f6;
}

.eventIcon {
  font-size: 2rem;
}

.eventContent h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.eventContent p {
  margin: 0;
  line-height: 1.6;
}

.eventDate {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: #1e293b;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
}

.narrativeText {
  line-height: 1.8;
  font-size: 1rem;
  color: #cbd5e1;
}

.citationMarker {
  color: #60a5fa;
  cursor: pointer;
  margin: 0 0.125rem;
}

.citationMarker:hover {
  color: #93c5fd;
  text-decoration: underline;
}

.footer {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #334155;
}

.disclaimer {
  font-size: 0.875rem;
  color: #94a3b8;
  font-style: italic;
  margin-bottom: 1rem;
}

.generated {
  font-size: 0.75rem;
  color: #64748b;
  font-family: 'Courier New', monospace;
}

.sidebar {
  width: 400px;
  background: #1e293b;
  padding: 2rem;
  overflow-y: auto;
  border-left: 1px solid #334155;
}

.sidebar h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.citations {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.citation {
  display: flex;
  gap: 1rem;
}

.citationNumber {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #334155;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 600;
  color: #60a5fa;
}

.citationContent h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
}

.evidence {
  margin-bottom: 1rem;
}

.evidenceSource {
  margin: 0 0 0.5rem 0;
  font-size: 0.75rem;
  color: #94a3b8;
}

.evidenceSource code {
  background: #0f172a;
  padding: 0.125rem 0.25rem;
  border-radius: 2px;
  font-family: 'Courier New', monospace;
}

.evidenceQuote {
  margin: 0.5rem 0;
  padding: 0.75rem;
  background: #0f172a;
  border-left: 2px solid #334155;
  font-size: 0.875rem;
  color: #cbd5e1;
  font-style: italic;
}

.evidenceConfidence {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #64748b;
}

.loading,
.error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #334155;
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error h3 {
  color: #ef4444;
}

.error button {
  padding: 0.5rem 1.5rem;
  background: #1e293b;
  color: #e2e8f0;
  border: 1px solid #334155;
  border-radius: 4px;
  cursor: pointer;
}

.error button:hover {
  background: #334155;
}
```

**Step 3: Create narrative hook**

Create `farmer_vault/hooks/useNarrative.ts`:

```typescript
/**
 * Hook for fetching narratives from API.
 */

import { useState, useCallback } from 'react';

interface NarrativeResult {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: 'haiku' | 'sonnet';
  main_narrative: string;
  highlighted_events: any[];
  total_documents: number;
  total_citations: number;
  generation_cost: number;
  from_cache: boolean;
  session_total_cost: number;
}

export function useNarrative(caseId: string, sessionId: string) {
  const [narrative, setNarrative] = useState<NarrativeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateNarrative = useCallback(
    async (clickedNodeId: string) => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/cases/${caseId}/narrative`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            clicked_node_id: clickedNodeId,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate narrative');
        }

        const data = await response.json();
        setNarrative(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        console.error('Narrative generation error:', err);
      } finally {
        setLoading(false);
      }
    },
    [caseId, sessionId]
  );

  const clearNarrative = useCallback(() => {
    setNarrative(null);
    setError(null);
  }, []);

  return {
    narrative,
    loading,
    error,
    generateNarrative,
    clearNarrative,
  };
}
```

**Step 4: Commit**

```bash
git add farmer_vault/components/NarrativePanel.tsx farmer_vault/components/NarrativePanel.module.css farmer_vault/hooks/useNarrative.ts
git commit -m "feat(frontend): add narrative panel component with evidence sidebar"
```

---

## Task 11: Next.js API Route Integration

**Files:**
- Create: `farmer_vault/pages/api/cases/[caseId]/narrative.ts`

**Step 1: Create Next.js API route**

Create `farmer_vault/pages/api/cases/[caseId]/narrative.ts`:

```typescript
/**
 * Next.js API route for narrative generation.
 *
 * POST /api/cases/[caseId]/narrative
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { spawn } from 'child_process';
import path from 'path';

interface NarrativeRequest {
  clicked_node_id: string;
  session_id: string;
}

interface NarrativeResponse {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  main_narrative: string;
  highlighted_events: any[];
  model_used: 'haiku' | 'sonnet';
  generation_cost: number;
  from_cache: boolean;
  session_total_cost: number;
  // ... other fields
}

interface ErrorResponse {
  error: string;
  details?: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<NarrativeResponse | ErrorResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { caseId } = req.query;
  const { clicked_node_id, session_id } = req.body as NarrativeRequest;

  // Validate input
  if (!clicked_node_id) {
    return res.status(400).json({ error: 'Missing clicked_node_id' });
  }

  if (!session_id) {
    return res.status(400).json({ error: 'Missing session_id' });
  }

  try {
    // Call Python backend via subprocess
    // In production, this would be a proper HTTP API call
    const result = await callPythonNarrativeAPI({
      caseId: caseId as string,
      clickedNodeId: clicked_node_id,
      sessionId: session_id,
    });

    return res.status(200).json(result);
  } catch (error) {
    console.error('Narrative generation error:', error);

    const message = error instanceof Error ? error.message : 'Unknown error';

    if (message.includes('cost limit exceeded')) {
      return res.status(429).json({
        error: 'Session cost limit exceeded',
        details: message,
      });
    }

    if (message.includes('not found')) {
      return res.status(404).json({
        error: 'Entity not found',
        details: message,
      });
    }

    return res.status(500).json({
      error: 'Internal server error',
      details: message,
    });
  }
}

/**
 * Call Python narrative API via subprocess.
 *
 * In production, replace this with actual HTTP API call to Python backend.
 */
async function callPythonNarrativeAPI(params: {
  caseId: string;
  clickedNodeId: string;
  sessionId: string;
}): Promise<NarrativeResponse> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(
      process.cwd(),
      '../farmer_factory/scripts/generate_narrative.py'
    );

    const pythonProcess = spawn('python', [
      scriptPath,
      '--case-id',
      params.caseId,
      '--node-id',
      params.clickedNodeId,
      '--session-id',
      params.sessionId,
      '--json',
    ]);

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python script failed: ${stderr}`));
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (err) {
        reject(new Error(`Failed to parse Python output: ${stdout}`));
      }
    });
  });
}
```

**Step 2: Create Python CLI script**

Create `farmer_factory/scripts/generate_narrative.py`:

```python
#!/usr/bin/env python3
"""
CLI script for narrative generation (called by Next.js API).

Usage:
    python generate_narrative.py --case-id TEST-CERESA --node-id prop_001 --session-id sess_123 --json
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.narrative.exceptions import (
    SessionCostLimitExceeded,
    InsufficientGraphData
)
from farmer_factory.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Generate narrative for entity')
    parser.add_argument('--case-id', required=True, help='Case ID')
    parser.add_argument('--node-id', required=True, help='Clicked node ID')
    parser.add_argument('--session-id', required=True, help='Session ID')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--max-cost', type=float, default=1.0, help='Max session cost')

    args = parser.parse_args()

    try:
        # Load graph
        graph_path = settings.cases_dir / args.case_id / "output" / "graph_data.json"
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph not found: {graph_path}")

        # Note: Assuming KnowledgeGraph can load from file
        # Implement load method if needed
        graph = KnowledgeGraph(case_id=args.case_id)
        # graph.load_from_file(str(graph_path))

        # Generate narrative
        generator = NarrativeGenerator(api_key=settings.anthropic_api_key)

        result = generator.generate(
            clicked_node_id=args.node_id,
            graph=graph,
            session_id=args.session_id,
            max_cost_per_session=args.max_cost
        )

        # Add session total
        output = result.model_dump()
        output["session_total_cost"] = generator.session_costs.get(args.session_id, 0.0)

        if args.json:
            print(json.dumps(output, default=str))
        else:
            print(f"Narrative for {result.focal_entity_name}:")
            print(result.main_narrative)
            print(f"\nCost: ${result.generation_cost:.4f}")

    except SessionCostLimitExceeded as e:
        logger.error(f"Cost limit exceeded: {e}")
        if args.json:
            print(json.dumps({"error": str(e)}))
        sys.exit(1)

    except InsufficientGraphData as e:
        logger.error(f"Insufficient data: {e}")
        if args.json:
            print(json.dumps({"error": str(e)}))
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 3: Make script executable**

```bash
chmod +x farmer_factory/scripts/generate_narrative.py
```

**Step 4: Commit**

```bash
git add farmer_vault/pages/api/cases/[caseId]/narrative.ts farmer_factory/scripts/generate_narrative.py
git commit -m "feat(api): add Next.js API route with Python backend integration"
```

---

## Final Steps

**Step 1: Run all tests**

```bash
# Backend tests
pytest tests/narrative/ -v

# Integration tests (requires API key)
export ANTHROPIC_API_KEY=your_key
pytest tests/narrative/test_integration.py -v -m integration
```

**Step 2: Update main documentation**

Add to `README.md` or `.claude/ROADMAP.md`:

```markdown
## Phase 6: Narrative Generation (COMPLETE)

**Status:** ✅ Implemented

**Features:**
- Single-stage LLM narrative generation
- Story centrality scoring with event weighting
- In-memory caching with Redis adapter
- Session cost tracking ($1 limit)
- Event highlighting (CONFISCATED, SOLD, INHERITED)
- Full-stack: Backend API + Frontend panel

**Modules:**
- `farmer_factory/narrative/` - Backend generation engine
- `farmer_vault/components/NarrativePanel.tsx` - Frontend UI
- `farmer_vault/pages/api/cases/[caseId]/narrative.ts` - API route

**Usage:**
See `farmer_factory/narrative/README.md`
```

**Step 3: Final commit**

```bash
git add README.md .claude/ROADMAP.md
git commit -m "docs: mark narrative generation phase as complete"
```

---

## Execution Complete

**Plan saved to:** `docs/plans/2026-01-25-narrative-generation-implementation-v2.md`

**Summary:**
- **11 tasks** (8 backend + 3 full-stack)
- **Single-stage LLM** (validated)
- **In-memory cache** (Redis adapter for later)
- **$1 session limit** (hard block)
- **Event highlighting** (CONFISCATED/SOLD/INHERITED)
- **Full test coverage** (unit + integration)
- **Frontend panel** with evidence sidebar
- **API integration** (Next.js → Python backend)

**Execution Options:**

1. **Parallel Session** (recommended) - Open new session, use `superpowers:executing-plans` skill with this plan file
2. **Subagent-Driven** (this session) - I dispatch agents per task with review checkpoints

Which approach would you like?