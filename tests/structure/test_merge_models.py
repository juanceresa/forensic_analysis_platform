"""Tests for merge authority Pydantic models."""

import pytest
from pydantic import ValidationError

from farmer_factory.structure.merge.models import (
    CrossTypeRelation,
    CrossTypeRelationsFile,
    EntityGroupFile,
    MergeGroup,
    MergeGroupMember,
    SameTypeRelation,
    UnmergedEntity,
)


def _member(id: str, name: str = "Test", source: str = "dedupe", confidence: float = 0.9):
    return MergeGroupMember(id=id, name=name, source=source, confidence=confidence)


def _group(canonical_id: str, members: list, status: str = "DRAFT"):
    return MergeGroup(
        canonical_id=canonical_id,
        canonical_name=members[0].name,
        status=status,
        members=members,
    )


class TestMergeGroupMember:
    def test_valid_member(self):
        m = _member("person_001", "Mario")
        assert m.id == "person_001"
        assert m.source == "dedupe"

    def test_empty_id_rejected(self):
        with pytest.raises(ValidationError):
            _member("  ", "Name")

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            _member("x", confidence=1.5)
        with pytest.raises(ValidationError):
            _member("x", confidence=-0.1)

    def test_source_literal(self):
        for src in ("dedupe", "analyst", "extraction"):
            _member("x", source=src)
        with pytest.raises(ValidationError):
            _member("x", source="unknown")


class TestMergeGroup:
    def test_canonical_must_be_first_member(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        with pytest.raises(ValidationError, match="canonical_id"):
            MergeGroup(canonical_id="b", canonical_name="B", members=[m1, m2])

    def test_valid_group(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        g = _group("a", [m1, m2])
        assert g.canonical_id == "a"
        assert len(g.members) == 2

    def test_minimum_one_member(self):
        with pytest.raises(ValidationError):
            MergeGroup(canonical_id="a", canonical_name="A", members=[])


class TestEntityGroupFile:
    def test_confirmed_top_requires_all_confirmed(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        g = _group("a", [m1, m2], status="DRAFT")
        with pytest.raises(ValidationError, match="CONFIRMED"):
            EntityGroupFile(status="CONFIRMED", groups=[g])

    def test_draft_top_allows_mixed(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        g = _group("a", [m1, m2], status="DRAFT")
        f = EntityGroupFile(status="DRAFT", groups=[g])
        assert f.status == "DRAFT"

    def test_all_confirmed_allows_confirmed_top(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        g = _group("a", [m1, m2], status="CONFIRMED")
        f = EntityGroupFile(status="CONFIRMED", groups=[g])
        assert f.status == "CONFIRMED"

    def test_duplicate_member_ids_rejected(self):
        m1 = _member("a", "A")
        m2 = _member("b", "B")
        m3 = _member("b", "B copy")  # duplicate
        m4 = _member("c", "C")
        g1 = _group("a", [m1, m2])
        g2 = _group("c", [m4, m3])  # m3 has id "b" which is in g1
        # Fix g2 canonical: c must be first
        # m3 id=b is a member, not canonical
        with pytest.raises(ValidationError, match="appears in groups"):
            EntityGroupFile(groups=[g1, g2])

    def test_empty_file_valid(self):
        f = EntityGroupFile()
        assert f.status == "DRAFT"
        assert f.groups == []

    def test_relations_draft_blocks_confirmed_top(self):
        rel = SameTypeRelation(
            source_id="a", target_id="b", relation_type="PARENT_OF", status="DRAFT"
        )
        with pytest.raises(ValidationError):
            EntityGroupFile(status="CONFIRMED", relations=[rel])


class TestCrossTypeRelationsFile:
    def test_confirmed_top_requires_all_confirmed(self):
        rel = CrossTypeRelation(
            source_id="a", target_id="b", relation_type="OWNS", status="DRAFT"
        )
        with pytest.raises(ValidationError):
            CrossTypeRelationsFile(status="CONFIRMED", relations=[rel])

    def test_valid_confirmed(self):
        rel = CrossTypeRelation(
            source_id="a", target_id="b", relation_type="OWNS", status="CONFIRMED"
        )
        f = CrossTypeRelationsFile(status="CONFIRMED", relations=[rel])
        assert f.status == "CONFIRMED"


class TestYamlRoundtrip:
    def test_entity_group_roundtrip(self):
        import yaml

        m1 = _member("a", "A")
        m2 = _member("b", "B")
        g = _group("a", [m1, m2], status="CONFIRMED")
        f = EntityGroupFile(
            status="CONFIRMED",
            extractions_hash="abc123",
            groups=[g],
            unmerged=[UnmergedEntity(id="c", name="C")],
        )
        dumped = yaml.dump(f.model_dump(), default_flow_style=False)
        loaded = yaml.safe_load(dumped)
        f2 = EntityGroupFile.model_validate(loaded)
        assert f2.status == "CONFIRMED"
        assert len(f2.groups) == 1
        assert f2.groups[0].canonical_id == "a"
        assert len(f2.unmerged) == 1

    def test_cross_type_roundtrip(self):
        import yaml

        rel = CrossTypeRelation(
            source_id="person_001",
            target_id="property_001",
            relation_type="OWNS",
            date="1952",
            status="CONFIRMED",
        )
        f = CrossTypeRelationsFile(
            status="CONFIRMED", extractions_hash="xyz", relations=[rel]
        )
        dumped = yaml.dump(f.model_dump(), default_flow_style=False)
        loaded = yaml.safe_load(dumped)
        f2 = CrossTypeRelationsFile.model_validate(loaded)
        assert len(f2.relations) == 1
        assert f2.relations[0].date == "1952"
