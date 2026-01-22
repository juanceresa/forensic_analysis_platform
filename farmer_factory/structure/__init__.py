"""
Graph structure module.
Builds knowledge graph using NetworkX.
Defines entity/relation schemas and graph construction logic.
"""

from .schema import (
    VerificationTier,
    Verification,
    EntityType,
    BaseEntity,
    Person,
    Property,
    Organization,
    Location,
    Document,
    RelationType,
    Relation,
    GraphMetadata,
    GraphExport,
)
from .graph import KnowledgeGraph
from .resolver import EntityResolver
from .builder import GraphBuilder
from .exporter import GraphExporter

__all__ = [
    "VerificationTier",
    "Verification",
    "EntityType",
    "BaseEntity",
    "Person",
    "Property",
    "Organization",
    "Location",
    "Document",
    "RelationType",
    "Relation",
    "GraphMetadata",
    "GraphExport",
    "KnowledgeGraph",
    "EntityResolver",
    "GraphBuilder",
    "GraphExporter",
]
