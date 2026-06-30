"""Artifact dependency graph tests (Task 82)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import ArtifactGraphStore, ArtifactRecord


def test_artifact_graph_contract(tmp_path):
    graph = ArtifactGraphStore(tmp_path, slug="demo_novel")
    graph.add(
        ArtifactRecord(
            id="outline_ch_001",
            type="outline",
            checksum="sha256:outline",
            provider="fake",
            prompt_version="p1",
        )
    )
    graph.add(
        ArtifactRecord(
            id="draft_ch_001_v1",
            type="draft",
            depends_on=["outline_ch_001"],
            checksum="sha256:draft",
            provider="fake",
            prompt_version="p2",
        )
    )
    payload = yaml.safe_load(graph.path.read_text(encoding="utf-8"))
    assert graph.path.name == "artifacts.graph.yaml"
    assert payload["artifacts"][1]["id"] == "draft_ch_001_v1"
    assert payload["artifacts"][1]["depends_on"] == ["outline_ch_001"]
    assert graph.trace("draft_ch_001_v1") == ["outline_ch_001", "draft_ch_001_v1"]


def test_artifact_graph_rejects_duplicate_ids(tmp_path):
    graph = ArtifactGraphStore(tmp_path, slug="demo_novel")
    graph.add(ArtifactRecord(id="draft", type="draft"))
    result = graph.add(ArtifactRecord(id="draft", type="draft"))
    assert result["status"] == "duplicate"
    assert len(graph.list()) == 1


def test_artifact_graph_cli_list_graph_trace(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    graph = ArtifactGraphStore(tmp_path / ".pf-agent" / "workspace", slug="demo_novel")
    graph.add(ArtifactRecord(id="outline_ch_001", type="outline"))
    graph.add(ArtifactRecord(id="draft_ch_001_v1", type="draft", depends_on=["outline_ch_001"]))
    assert main(["artifacts", "list", "--slug", "demo_novel"]) == 0
    assert main(["artifacts", "graph", "--slug", "demo_novel"]) == 0
    assert main(["artifacts", "trace", "draft_ch_001_v1", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "draft_ch_001_v1" in out
    assert "outline_ch_001 -> draft_ch_001_v1" in out
