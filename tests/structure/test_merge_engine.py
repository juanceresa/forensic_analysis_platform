"""Tests for merge engine (apply-merges)."""

import json
import pytest
import yaml
from pathlib import Path

from farmer_factory.structure.merge_engine import apply_merges
from farmer_factory.structure.merge_writer import write_entity_groups, write_cross_type_relations


@pytest.fixture
def case_dir(tmp_path):
    extractions = tmp_path / "extractions"
    extractions.mkdir()
    (extractions / "doc1.json").write_text("{}")
    (tmp_path / "output").mkdir()
    (tmp_path / "entity_groups").mkdir()
    return tmp_path


def _write_graph(case_dir: Path, nodes: list, links: list):
    graph = {"nodes": nodes, "links": links, "metadata": {}}
    path = case_dir / "output" / "graph_data.json"
    path.write_text(json.dumps(graph))
    return path


def _make_nodes():
    return [
        {"id": "person_a", "name": "Alice", "entity_type": "PERSON",
         "extracted_from": "doc1", "verification": {"confidence": 0.9, "tier": "TIER_3_AI"}},
        {"id": "person_b", "name": "Alise", "entity_type": "PERSON",
         "extracted_from": "doc2", "profession": "Notary",
         "verification": {"confidence": 0.7, "tier": "TIER_3_AI"}},
        {"id": "person_c", "name": "Carlos", "entity_type": "PERSON",
         "extracted_from": "doc1", "verification": {"confidence": 0.8, "tier": "TIER_3_AI"}},
        {"id": "property_x", "name": "Villa", "entity_type": "PROPERTY",
         "extracted_from": "doc1", "verification": {"confidence": 0.9, "tier": "TIER_3_AI"}},
    ]


class TestApplyMerges:
    def test_no_merges_returns_unchanged(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])
        path = apply_merges(case_dir)
        data = json.loads(path.read_text())
        assert len(data["nodes"]) == 4

    def test_merge_removes_member_node(self, case_dir):
        nodes = _make_nodes()
        links = [{"source": "person_a", "target": "property_x", "relation_type": "OWNS",
                  "verification": {"confidence": 0.9}}]
        _write_graph(case_dir, nodes, links)

        # Write confirmed merge: b → a
        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        result = apply_merges(case_dir)
        graph = json.loads(result.read_text())
        ids = [n["id"] for n in graph["nodes"]]
        assert "person_a" in ids
        assert "person_b" not in ids
        assert len(graph["nodes"]) == 3

    def test_merged_node_combines_extracted_from(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        alice = next(n for n in graph["nodes"] if n["id"] == "person_a")
        sources = set(alice["extracted_from"].split(","))
        assert "doc1" in sources
        assert "doc2" in sources

    def test_merged_node_fills_missing_fields(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        alice = next(n for n in graph["nodes"] if n["id"] == "person_a")
        # person_a had no profession, person_b had "Notary"
        assert alice["profession"] == "Notary"

    def test_relation_rewriting(self, case_dir):
        nodes = _make_nodes()
        links = [
            {"source": "person_b", "target": "property_x", "relation_type": "OWNS",
             "verification": {"confidence": 0.8}},
        ]
        _write_graph(case_dir, nodes, links)

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert all(l["source"] != "person_b" for l in graph["links"])
        owns = [l for l in graph["links"] if l["relation_type"] == "OWNS"]
        assert len(owns) == 1
        assert owns[0]["source"] == "person_a"

    def test_self_loop_removed(self, case_dir):
        nodes = _make_nodes()
        links = [
            {"source": "person_a", "target": "person_b", "relation_type": "SAME_AS",
             "verification": {"confidence": 0.9}},
        ]
        _write_graph(case_dir, nodes, links)

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["links"]) == 0

    def test_duplicate_relation_dedup_keeps_higher_confidence(self, case_dir):
        nodes = _make_nodes()
        links = [
            {"source": "person_a", "target": "property_x", "relation_type": "OWNS",
             "verification": {"confidence": 0.5}},
            {"source": "person_b", "target": "property_x", "relation_type": "OWNS",
             "verification": {"confidence": 0.9}},
        ]
        _write_graph(case_dir, nodes, links)

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        owns = [l for l in graph["links"] if l["relation_type"] == "OWNS"]
        assert len(owns) == 1
        assert owns[0]["verification"]["confidence"] == 0.9

    def test_bidirectional_edges_preserved(self, case_dir):
        nodes = _make_nodes()
        links = [
            {"source": "person_a", "target": "person_c", "relation_type": "PARENT_OF",
             "verification": {"confidence": 0.9}},
            {"source": "person_c", "target": "person_a", "relation_type": "CHILD_OF",
             "verification": {"confidence": 0.9}},
        ]
        _write_graph(case_dir, nodes, links)
        # No merges, just verify bidirectional preserved
        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["links"]) == 2

    def test_draft_skipped_by_default(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        write_entity_groups(case_dir, "PERSON", clusters, [])
        # All DRAFT — should not merge

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["nodes"]) == 4

    def test_include_drafts_applies_draft_merges(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        write_entity_groups(case_dir, "PERSON", clusters, [])

        apply_merges(case_dir, include_drafts=True)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["nodes"]) == 3

    def test_idempotent(self, case_dir):
        nodes = _make_nodes()
        links = [{"source": "person_b", "target": "property_x", "relation_type": "OWNS",
                  "verification": {"confidence": 0.8}}]
        _write_graph(case_dir, nodes, links)

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        first = json.loads((case_dir / "output" / "graph_data.json").read_text())

        apply_merges(case_dir)
        second = json.loads((case_dir / "output" / "graph_data.json").read_text())

        assert len(first["nodes"]) == len(second["nodes"])
        assert len(first["links"]) == len(second["links"])

    def test_missing_entity_ids_skipped(self, case_dir):
        nodes = [{"id": "person_a", "name": "Alice", "entity_type": "PERSON",
                  "extracted_from": "doc1"}]
        _write_graph(case_dir, nodes, [])

        # Merge references non-existent person_z
        clusters = [[("person_a", "Alice", 0.95), ("person_z", "Ghost", 0.5)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        path.write_text(yaml.dump(data, default_flow_style=False))

        # Should not crash
        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["nodes"]) == 1

    def test_no_graph_raises(self, case_dir):
        with pytest.raises(FileNotFoundError):
            apply_merges(case_dir)

    def test_cross_type_relations_applied(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        # Write confirmed cross-type relation
        write_cross_type_relations(case_dir, [
            {"source_id": "person_a", "target_id": "property_x",
             "relation_type": "OWNS", "date": "1952"},
        ])
        ct_path = case_dir / "entity_groups" / "cross_type_relations.yaml"
        data = yaml.safe_load(ct_path.read_text())
        data["status"] = "CONFIRMED"
        data["relations"][0]["status"] = "CONFIRMED"
        ct_path.write_text(yaml.dump(data, default_flow_style=False))

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        owns = [l for l in graph["links"] if l["relation_type"] == "OWNS"]
        assert len(owns) == 1

    def test_draft_cross_type_skipped_by_default(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        write_cross_type_relations(case_dir, [
            {"source_id": "person_a", "target_id": "property_x",
             "relation_type": "OWNS"},
        ])
        # Leave as DRAFT

        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["links"]) == 0

    def test_stale_hash_warns_but_proceeds(self, case_dir):
        nodes = _make_nodes()
        _write_graph(case_dir, nodes, [])

        clusters = [[("person_a", "Alice", 0.95), ("person_b", "Alise", 0.85)]]
        path = write_entity_groups(case_dir, "PERSON", clusters, [])
        data = yaml.safe_load(path.read_text())
        data["status"] = "CONFIRMED"
        data["groups"][0]["status"] = "CONFIRMED"
        data["extractions_hash"] = "stale_old_hash"
        path.write_text(yaml.dump(data, default_flow_style=False))

        # Add new extraction file to change the hash
        (case_dir / "extractions" / "doc_new.json").write_text("{}")

        # Should not crash — just warn
        apply_merges(case_dir)
        graph = json.loads((case_dir / "output" / "graph_data.json").read_text())
        assert len(graph["nodes"]) == 3
