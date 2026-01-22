"""Unit tests for Graph Builder."""

import pytest
from farmer_factory.structure.builder import GraphBuilder
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.schema import (
    Person, Property, EntityType, Verification, VerificationTier,
    Relation, RelationType
)
from farmer_factory.prepare import DocumentPath


def test_builder_initialization():
    """Test GraphBuilder can be initialized."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()

    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    assert builder is not None
    assert builder.graph == graph
    assert builder.resolver == resolver
    assert builder.processing_stats == {
        "documents_processed": 0,
        "entities_extracted": 0,
        "entities_merged": 0,
        "relations_added": 0
    }


def test_add_extraction_single_entity():
    """Test adding extraction with single entity."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create extraction result with one person
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    extraction = ExtractionResult(
        entities=[person],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path=DocumentPath.HANDWRITTEN,
        processing_metadata={}
    )

    builder.add_extraction(extraction)

    # Verify entity was added
    assert graph.graph.number_of_nodes() == 1
    assert graph.get_entity("p1") is not None

    # Verify stats
    assert builder.processing_stats["documents_processed"] == 1
    assert builder.processing_stats["entities_extracted"] == 1
    assert builder.processing_stats["entities_merged"] == 0
    assert builder.processing_stats["relations_added"] == 0


def test_add_extraction_with_relation():
    """Test adding extraction with entity and relation."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create person and property
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    property_entity = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca en Miramar",
        property_type="residential",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    # Create ownership relation
    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        )
    )

    extraction = ExtractionResult(
        entities=[person, property_entity],
        relations=[relation],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path=DocumentPath.HANDWRITTEN,
        processing_metadata={}
    )

    builder.add_extraction(extraction)

    # Verify entities and relation were added
    assert graph.graph.number_of_nodes() == 2
    assert graph.graph.number_of_edges() == 1

    # Verify stats
    assert builder.processing_stats["entities_extracted"] == 2
    assert builder.processing_stats["relations_added"] == 1


def test_add_extraction_with_merge():
    """Test adding extraction that merges with existing entity."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver(similarity_threshold=0.85)
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # First extraction
    person1 = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez García",
        birth_date="1920",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    extraction1 = ExtractionResult(
        entities=[person1],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path=DocumentPath.HANDWRITTEN,
        processing_metadata={}
    )

    builder.add_extraction(extraction1)

    # Second extraction (similar person, different birth date)
    person2 = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Perez Garcia",  # Similar name, no accents
        birth_date="1922",  # Conflicting birth date
        alternate_names=[],
        roles=["seller"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    extraction2 = ExtractionResult(
        entities=[person2],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.85},
        path=DocumentPath.HANDWRITTEN,
        processing_metadata={}
    )

    builder.add_extraction(extraction2)

    # Should still have 1 node (merged)
    assert graph.graph.number_of_nodes() == 1

    # Verify stats
    assert builder.processing_stats["entities_extracted"] == 2
    assert builder.processing_stats["entities_merged"] == 1

    # Verify merge
    entity_data = graph.get_entity("p1")
    assert isinstance(entity_data["birth_date"], list)  # Conflicting dates
    assert set(entity_data["roles"]) == {"owner", "seller"}  # Merged roles
