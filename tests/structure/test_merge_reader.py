"""Tests for merge authority YAML reader."""

import pytest
import yaml
from pathlib import Path

from farmer_factory.structure.merge_reader import (
    read_entity_groups,
    read_cross_type_relations,
    get_confirmed_merges,
    get_all_entity_groups,
)
from farmer_factory.structure.merge_writer import write_entity_groups, write_cross_type_relations


@pytest.fixture
def case_dir(tmp_path):
    extractions = tmp_path / "extractions"
    extractions.mkdir()
    (extractions / "doc1.json").write_text("{}")
    return tmp_path


class TestReadEntityGroups:
    def test_returns_none_for_missing_file(self, case_dir):
        assert read_entity_groups(case_dir, "PERSON") is None

    def test_reads_written_file(self, case_dir):
        clusters = [[("a", "A", 0.9), ("b", "B", 0.8)]]
        write_entity_groups(case_dir, "PERSON", clusters, [("c", "C")])
        result = read_entity_groups(case_dir, "PERSON")
        assert result is not None
        assert len(result.groups) == 1
        assert len(result.unmerged) == 1

    def test_unknown_type_raises(self, case_dir):
        with pytest.raises(ValueError):
            read_entity_groups(case_dir, "BOGUS")


class TestReadCrossTypeRelations:
    def test_returns_none_for_missing(self, case_dir):
        assert read_cross_type_relations(case_dir) is None

    def test_reads_written_file(self, case_dir):
        write_cross_type_relations(case_dir, [
            {"source_id": "a", "target_id": "b", "relation_type": "OWNS"},
        ])
        result = read_cross_type_relations(case_dir)
        assert result is not None
        assert len(result.relations) == 1


class TestGetConfirmedMerges:
    def test_empty_when_no_files(self, case_dir):
        assert get_confirmed_merges(case_dir) == {}

    def test_skips_draft_by_default(self, case_dir):
        clusters = [[("a", "A", 0.9), ("b", "B", 0.8)]]
        write_entity_groups(case_dir, "PERSON", clusters, [])
        # All DRAFT
        assert get_confirmed_merges(case_dir) == {}

    def test_returns_confirmed_merges(self, case_dir):
        clusters = [[("a", "A", 0.9), ("b", "B", 0.8)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        # Manually confirm
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        merges = get_confirmed_merges(case_dir)
        assert merges == {"b": "a"}

    def test_include_drafts_returns_all(self, case_dir):
        clusters = [[("a", "A", 0.9), ("b", "B", 0.8)]]
        write_entity_groups(case_dir, "PERSON", clusters, [])
        merges = get_confirmed_merges(case_dir, include_drafts=True)
        assert merges == {"b": "a"}

    def test_canonical_not_in_map(self, case_dir):
        clusters = [[("a", "A", 0.9), ("b", "B", 0.8), ("c", "C", 0.7)]]
        write_entity_groups(case_dir, "PERSON", clusters, [])
        merges = get_confirmed_merges(case_dir, include_drafts=True)
        assert "a" not in merges
        assert merges["b"] == "a"
        assert merges["c"] == "a"


class TestGetAllEntityGroups:
    def test_empty_when_no_files(self, case_dir):
        assert get_all_entity_groups(case_dir) == []

    def test_returns_existing_files(self, case_dir):
        write_entity_groups(case_dir, "PERSON", [], [("a", "A")])
        write_entity_groups(case_dir, "PROPERTY", [], [("b", "B")])
        results = get_all_entity_groups(case_dir)
        types = [t for t, _ in results]
        assert "PERSON" in types
        assert "PROPERTY" in types
