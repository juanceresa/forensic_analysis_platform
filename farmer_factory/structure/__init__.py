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
from .dedupe.resolver import DedupeEntityResolver
from .core.builder import GraphBuilder
from .core.exporter import GraphExporter

# Backward compatibility alias (deprecated, use DedupeEntityResolver)
EntityResolver = DedupeEntityResolver

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
    "DedupeEntityResolver",
    "EntityResolver",  # Deprecated alias
    "GraphBuilder",
    "GraphExporter",
]
