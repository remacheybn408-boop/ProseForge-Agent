"""Relationship graph tests (Task 94)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, RelationshipGraph


def test_relationship_graph_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    graph = RelationshipGraph(tmp_path, slug="demo_novel")
    relation = graph.add_relation(
        source="char_001",
        target="char_002",
        type="friend",
        evidence=["ch_001"],
    )

    assert relation.type == "friend"
    assert graph.list()[0].source == "char_001"

    data = graph.graph(format="json")
    assert data["nodes"] == ["char_001", "char_002"]
    assert data["edges"][0]["type"] == "friend"

    dot = graph.graph(format="dot")
    assert '"char_001" -> "char_002" [label="friend"]' in dot

    evidence = graph.evidence("char_001")
    assert evidence[0]["type"] == "relationship"
    assert "char_002" in evidence[0]["text"]


def test_relationship_graph_rejects_unknown_relation_type(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    graph = RelationshipGraph(tmp_path, slug="demo_novel")

    try:
        graph.add_relation(source="char_001", target="char_002", type="stranger")
    except ValueError as exc:
        assert "unknown relation type" in str(exc)
    else:
        raise AssertionError("unknown relation type should fail")


def test_relation_cli_add_list_graph(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert (
        main(
            [
                "relation",
                "add",
                "--slug",
                "demo_novel",
                "--source",
                "char_001",
                "--target",
                "char_002",
                "--type",
                "friend",
                "--evidence",
                "ch_001",
            ]
        )
        == 0
    )
    assert main(["relation", "list", "--slug", "demo_novel"]) == 0
    assert main(["relation", "graph", "--slug", "demo_novel", "--graph-format", "dot"]) == 0
    out = capsys.readouterr().out
    assert "Relationship Graph" in out
    assert "char_001" in out
    assert "friend" in out
