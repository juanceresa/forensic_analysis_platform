"""Tests for merge authority YAML writer."""

import pytest
import yaml
from pathlib import Path

from farmer_factory.structure.merge_models import EntityGroupFile, MergeGroup, MergeGroupMember
from farmer_factory.structure.merge_writer import (
    write_entity_groups,
    write_cross_type_relations,
    add_analyst_merge,
)


@pytest.fixture
def case_dir(tmp_path):
    """Create a minimal case directory."""
    extractions = tmp_path / "extractions"
    extractions.mkdir()
    (extractions / "doc1.json").write_text("{}")
    (extractions / "doc2.json").write_text("{}")
    return tmp_path


def _load_yaml(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


class TestWriteEntityGroups:
    def test_writes_draft_groups(self, case_dir):
        clusters = [
            [("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)],
        ]
        singletons = [("person_c", "Carlos")]

        path = write_entity_groups(case_dir, "PERSON", clusters, singletons)

        assert path.exists()
        data = _load_yaml(path)
        assert data["status"] == "DRAFT"
        assert len(data["groups"]) == 1
        assert data["groups"][0]["canonical_id"] == "person_a"
        assert len(data["groups"][0]["members"]) == 2
        assert len(data["unmerged"]) == 1

    def test_preserves_confirmed_on_update(self, case_dir):
        # First write: one confirmed group
        clusters = [
            [("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)],
        ]
        write_entity_groups(case_dir, "PERSON", clusters, [])

        # Manually confirm
        path = case_dir / "entity_groups" / "person_groups.yaml"
        data = _load_yaml(path)
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        # Second write: new cluster with overlapping member
        new_clusters = [
            [("person_a", "Alice", 0.9), ("person_d", "Dave", 0.7)],
            [("person_e", "Eve", 0.8), ("person_f", "Frank", 0.75)],
        ]
        write_entity_groups(case_dir, "PERSON", new_clusters, [])

        data2 = _load_yaml(path)
        # Top-level should be DRAFT (new entries added)
        assert data2["status"] == "DRAFT"
        # Confirmed group preserved
        confirmed = [g for g in data2["groups"] if g["status"] == "CONFIRMED"]
        assert len(confirmed) == 1
        assert confirmed[0]["canonical_id"] == "person_a"
        # New draft group added (person_e + person_f; person_a and person_d filtered)
        draft = [g for g in data2["groups"] if g["status"] == "DRAFT"]
        assert len(draft) == 1
        assert draft[0]["canonical_id"] == "person_e"

    def test_top_level_draft_when_new_entries(self, case_dir):
        clusters = [
            [("x", "X", 0.9), ("y", "Y", 0.8)],
        ]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = _load_yaml(path)
        assert data["status"] == "DRAFT"

    def test_unknown_entity_type_raises(self, case_dir):
        with pytest.raises(ValueError, match="Unknown entity type"):
            write_entity_groups(case_dir, "INVALID", [], [])

    def test_extractions_hash_populated(self, case_dir):
        path = write_entity_groups(case_dir, "PERSON", [], [("s", "S")])
        data = _load_yaml(path)
        assert data["extractions_hash"]
        assert len(data["extractions_hash"]) == 12


class TestWriteCrossTypeRelations:
    def test_writes_draft_relations(self, case_dir):
        relations = [
            {"source_id": "person_a", "target_id": "property_b", "relation_type": "OWNS", "date": "1952"},
        ]
        path = write_cross_type_relations(case_dir, relations)
        data = _load_yaml(path)
        assert data["status"] == "DRAFT"
        assert len(data["relations"]) == 1
        assert data["relations"][0]["relation_type"] == "OWNS"

    def test_preserves_confirmed_relations(self, case_dir):
        relations = [
            {"source_id": "a", "target_id": "b", "relation_type": "OWNS"},
        ]
        path = write_cross_type_relations(case_dir, relations)

        # Confirm
        data = _load_yaml(path)
        data["status"] = "CONFIRMED"
        data["relations"][0]["status"] = "CONFIRMED"
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        # Write again with new relation
        new_relations = [
            {"source_id": "a", "target_id": "b", "relation_type": "OWNS"},  # dupe
            {"source_id": "c", "target_id": "d", "relation_type": "CONFISCATED"},
        ]
        write_cross_type_relations(case_dir, new_relations)
        data2 = _load_yaml(path)
        assert data2["status"] == "DRAFT"
        confirmed = [r for r in data2["relations"] if r["status"] == "CONFIRMED"]
        draft = [r for r in data2["relations"] if r["status"] == "DRAFT"]
        assert len(confirmed) == 1
        assert len(draft) == 1


class TestAddAnalystMerge:
    def test_creates_new_group(self, case_dir):
        path = add_analyst_merge(
            case_dir, "PERSON", "person_a", "Alice", "person_b", "Alise"
        )
        data = _load_yaml(path)
        assert len(data["groups"]) == 1
        g = data["groups"][0]
        assert g["canonical_id"] == "person_a"
        assert g["status"] == "CONFIRMED"
        assert len(g["members"]) == 2
        assert g["members"][1]["source"] == "analyst"
        assert g["members"][1]["confidence"] == 1.0

    def test_adds_to_existing_group(self, case_dir):
        add_analyst_merge(case_dir, "PERSON", "person_a", "Alice", "person_b", "Alise")
        add_analyst_merge(case_dir, "PERSON", "person_a", "Alice", "person_c", "Alicia")

        path = case_dir / "entity_groups" / "person_groups.yaml"
        data = _load_yaml(path)
        assert len(data["groups"]) == 1
        assert len(data["groups"][0]["members"]) == 3
