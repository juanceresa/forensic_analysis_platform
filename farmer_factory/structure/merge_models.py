"""Pydantic models for entity merge authority YAML files.

Defines the schema for entity group merge files and cross-type relation files.
These YAML files serve as the single source of truth for all entity merge decisions,
supporting analyst review with a two-level DRAFT/CONFIRMED status system.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Status Types
# ============================================================================

StatusType = Literal["DRAFT", "CONFIRMED"]
SourceType = Literal["dedupe", "analyst", "extraction"]


# ============================================================================
# Entity Group Models
# ============================================================================


class MergeGroupMember(BaseModel):
    """A single entity that belongs to a merge group."""

    id: str
    name: str
    source: SourceType
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Member id must not be empty")
        return v


class MergeGroup(BaseModel):
    """A group of entities that should be merged into a single canonical entity."""

    canonical_id: str
    canonical_name: str
    status: StatusType = "DRAFT"
    members: List[MergeGroupMember] = Field(min_length=1)

    @model_validator(mode="after")
    def canonical_is_first_member(self) -> "MergeGroup":
        """Canonical ID must match the first member's ID."""
        if self.members and self.members[0].id != self.canonical_id:
            raise ValueError(
                f"canonical_id '{self.canonical_id}' must match first member id "
                f"'{self.members[0].id}'"
            )
        return self


class SameTypeRelation(BaseModel):
    """A relation between entities of the same type (e.g., PARENT_OF between persons)."""

    source_id: str
    target_id: str
    relation_type: str
    date: Optional[str] = None
    source: SourceType = "extraction"
    status: StatusType = "DRAFT"


class UnmergedEntity(BaseModel):
    """An entity that doesn't belong to any merge group (singleton)."""

    id: str
    name: str


class EntityGroupFile(BaseModel):
    """Top-level model for an entity type's merge file (e.g., person_groups.yaml)."""

    status: StatusType = "DRAFT"
    extractions_hash: str = ""
    groups: List[MergeGroup] = Field(default_factory=list)
    relations: List[SameTypeRelation] = Field(default_factory=list)
    unmerged: List[UnmergedEntity] = Field(default_factory=list)

    @model_validator(mode="after")
    def status_reflects_entries(self) -> "EntityGroupFile":
        """Top-level CONFIRMED only if all entries are CONFIRMED."""
        if self.status == "CONFIRMED":
            for group in self.groups:
                if group.status != "CONFIRMED":
                    raise ValueError(
                        f"Top-level status is CONFIRMED but group "
                        f"'{group.canonical_id}' is DRAFT"
                    )
            for rel in self.relations:
                if rel.status != "CONFIRMED":
                    raise ValueError(
                        "Top-level status is CONFIRMED but a relation is DRAFT"
                    )
        return self

    @model_validator(mode="after")
    def no_duplicate_member_ids(self) -> "EntityGroupFile":
        """An entity ID may appear in at most one group."""
        seen: dict[str, str] = {}
        for group in self.groups:
            for member in group.members:
                if member.id in seen:
                    raise ValueError(
                        f"Entity '{member.id}' appears in groups "
                        f"'{seen[member.id]}' and '{group.canonical_id}'"
                    )
                seen[member.id] = group.canonical_id
        return self


# ============================================================================
# Cross-Type Relation Models
# ============================================================================


class CrossTypeRelation(BaseModel):
    """A relation between entities of different types (e.g., person OWNS property)."""

    source_id: str
    target_id: str
    relation_type: str
    date: Optional[str] = None
    source: SourceType = "dedupe"
    status: StatusType = "DRAFT"


class CrossTypeRelationsFile(BaseModel):
    """Top-level model for cross-type relations file (cross_type_relations.yaml)."""

    status: StatusType = "DRAFT"
    extractions_hash: str = ""
    relations: List[CrossTypeRelation] = Field(default_factory=list)

    @model_validator(mode="after")
    def status_reflects_entries(self) -> "CrossTypeRelationsFile":
        """Top-level CONFIRMED only if all relations are CONFIRMED."""
        if self.status == "CONFIRMED":
            for rel in self.relations:
                if rel.status != "CONFIRMED":
                    raise ValueError(
                        "Top-level status is CONFIRMED but a relation is DRAFT"
                    )
        return self
