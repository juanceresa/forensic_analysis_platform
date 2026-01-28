"""Unit tests for Graph Builder."""

import pytest
from farmer_factory.structure.builder import GraphBuilder
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.structure.resolver import DedupeEntityResolver
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.schema import (
    Person, Property, EntityType, Verification, VerificationTier,
    Relation, RelationType
)
from farmer_factory.prepare import DocumentPath


def test_builder_initialization():
    """Test GraphBuilder can be initialized."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = DedupeEntityResolver()

    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    assert builder is not None
    assert builder.graph == graph
    assert builder.resolver == resolver
    assert builder.processing_stats == {
        "documents_processed": 0,
        "entities_extracted": 0,
        "entities_merged": 0,
        "relations_added": 0,
        "document_groups_used": 0,
    }


def test_add_extraction_single_entity():
    """Test adding extraction with single entity."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = DedupeEntityResolver()
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

    # Verify entity was added (person + auto-created DOCUMENT)
    assert graph.graph.number_of_nodes() == 2
    assert graph.get_entity("p1") is not None

    # Verify stats (entities_extracted includes the auto-created DOCUMENT)
    assert builder.processing_stats["documents_processed"] == 1
    assert builder.processing_stats["entities_extracted"] == 2  # 1 person + 1 DOCUMENT
    assert builder.processing_stats["entities_merged"] == 0
    assert builder.processing_stats["relations_added"] == 0


def test_add_extraction_with_relation():
    """Test adding extraction with entity and relation."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = DedupeEntityResolver()
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

    # Verify entities and relation were added (person + property + auto-created DOCUMENT)
    assert graph.graph.number_of_nodes() == 3
    assert graph.graph.number_of_edges() == 1

    # Verify stats (entities_extracted includes the auto-created DOCUMENT)
    assert builder.processing_stats["entities_extracted"] == 3  # 2 entities + 1 DOCUMENT
    assert builder.processing_stats["relations_added"] == 1


def test_add_extraction_with_merge():
    """Test adding extraction that merges with existing entity."""
    from unittest.mock import Mock

    graph = KnowledgeGraph(case_id="test_case")
    resolver = Mock()

    # Configure resolver to return p1 as match for p2, None for p1
    def find_similar(entity, graph):
        if entity.id == "p2":
            return ("p1", 0.7)
        return None

    def merge_func(existing, new, match_confidence=0.8):
        existing_sources = existing.get("extracted_from", [])
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources]
        new_sources = [new.extracted_from] if isinstance(new.extracted_from, str) else new.extracted_from

        return {
            **existing,
            "birth_date": [f"{existing['birth_date']} (doc_001)", f"{new.birth_date} (doc_002)"],
            "roles": list(set(existing.get("roles", []) + new.roles)),
            "extracted_from": ",".join(list(set(existing_sources + new_sources)))
        }

    resolver.find_similar_entity = Mock(side_effect=find_similar)
    resolver.merge_entities = Mock(side_effect=merge_func)

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

    # Should have 2 nodes (1 person merged + 2 DOCUMENT entities from 2 extractions)
    assert graph.graph.number_of_nodes() == 3

    # Verify stats (entities_extracted includes 2 auto-created DOCUMENT entities)
    assert builder.processing_stats["entities_extracted"] == 4  # 2 persons + 2 DOCUMENTs
    assert builder.processing_stats["entities_merged"] == 1

    # Verify merge
    entity_data = graph.get_entity("p1")
    assert isinstance(entity_data["birth_date"], list)  # Conflicting dates
    assert set(entity_data["roles"]) == {"owner", "seller"}  # Merged roles
    resolver.merge_entities.assert_called()
    assert resolver.merge_entities.call_args.kwargs["match_confidence"] == 0.7


def test_add_extraction_with_merge_and_relations():
    """Test that relations are remapped correctly when entities are merged."""
    from unittest.mock import Mock

    graph = KnowledgeGraph(case_id="test_case")
    resolver = Mock()

    # Configure resolver to merge p2 into p1, no match for others
    def find_similar(entity, graph):
        if entity.id == "p2":
            return ("p1", 0.9)
        return None

    def merge_func(existing, new, match_confidence=0.8):
        existing_sources = existing.get("extracted_from", [])
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources]
        new_sources = [new.extracted_from] if isinstance(new.extracted_from, str) else new.extracted_from

        return {
            **existing,
            "roles": list(set(existing.get("roles", []) + new.roles)),
            "extracted_from": ",".join(list(set(existing_sources + new_sources)))
        }

    resolver.find_similar_entity = Mock(side_effect=find_similar)
    resolver.merge_entities = Mock(side_effect=merge_func)

    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # First extraction: person + property + relation
    person1 = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.92,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    property1 = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca Aguaras",
        property_type="Farm",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    relation1 = Relation(
        id="rel1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90
        )
    )

    extraction1 = ExtractionResult(
        entities=[person1, property1],
        relations=[relation1],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.90},
        path=DocumentPath.TYPED,
        processing_metadata={}
    )

    builder.add_extraction(extraction1)

    # Verify first extraction (person + property + auto-created DOCUMENT)
    assert graph.graph.number_of_nodes() == 3
    assert graph.graph.number_of_edges() == 1

    # Second extraction: similar person + new property + relation
    # This person should merge with p1
    person2 = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Mario F. Ceresa",  # Similar name, will merge
        alternate_names=[],
        roles=["heir"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    property2 = Property(
        id="prop2",
        entity_type=EntityType.PROPERTY,
        name="Casa Habana",
        property_type="House",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    # Relation references p2, which will be merged into p1
    relation2 = Relation(
        id="rel2",
        type=RelationType.OWNS,
        source_id="p2",  # This ID will be remapped to p1
        target_id="prop2",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88
        )
    )

    extraction2 = ExtractionResult(
        entities=[person2, property2],
        relations=[relation2],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path=DocumentPath.TYPED,
        processing_metadata={}
    )

    builder.add_extraction(extraction2)

    # Verify merge: 1 merged person + 2 properties + 2 DOCUMENT entities = 5 nodes
    assert graph.graph.number_of_nodes() == 5

    # CRITICAL: Should have 2 relations, not 1 (the second relation should be added successfully)
    assert graph.graph.number_of_edges() == 2

    # Verify stats (entities_extracted includes 2 auto-created DOCUMENT entities)
    assert builder.processing_stats["entities_extracted"] == 6  # 4 entities + 2 DOCUMENTs
    assert builder.processing_stats["entities_merged"] == 1
    assert builder.processing_stats["relations_added"] == 2  # Both relations should be added

    # Verify the merged person has both roles
    entity_data = graph.get_entity("p1")
    assert set(entity_data["roles"]) == {"owner", "heir"}


def test_build_from_document_batch():
    """Test processing multiple extractions in batch."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = DedupeEntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create multiple extractions
    extractions = []
    names = ["Juan Pérez", "María López", "Carlos García"]

    for i, name in enumerate(names):
        person = Person(
            id=f"p{i}",
            entity_type=EntityType.PERSON,
            name=name,
            alternate_names=[],
            roles=[],
            verification=Verification(
                tier=VerificationTier.TIER_3_AI,
                confidence=0.88,
                verified_by=None,
                verified_at=None,
                notes=None
            ),
            extracted_from=f"doc_00{i}"
        )

        extraction = ExtractionResult(
            entities=[person],
            relations=[],
            ocr_result=None,
            confidence_scores={"vision_confidence": 0.88},
            path=DocumentPath.HANDWRITTEN,
            processing_metadata={}
        )

        extractions.append(extraction)

    builder.build_from_document_batch(extractions)

    # Verify all entities added (3 persons + 3 auto-created DOCUMENT entities)
    assert graph.graph.number_of_nodes() == 6
    assert builder.processing_stats["documents_processed"] == 3
    assert builder.processing_stats["entities_extracted"] == 6  # 3 persons + 3 DOCUMENTs
