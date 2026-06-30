"""Scene-level workflow tests (Task 84)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, SceneWorkflow


def test_scene_level_workflow_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    workflow = SceneWorkflow(tmp_path, slug="demo_novel")
    scene = workflow.draft(
        chapter_id="ch_001",
        scene_id="sc_001",
        goal="Open with conflict",
        location="market",
        characters=["A", "B"],
        conflict="A refuses B",
        emotional_tone="tense",
    )
    assert scene.id == "sc_001"
    assert scene.status == "drafted"
    assert scene.output_file.exists()
    manifest = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["structure"]["scenes"][0]["id"] == "sc_001"
    assert manifest["structure"]["scenes"][0]["chapter_id"] == "ch_001"


def test_scene_review_rewrite_and_merge(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    workflow = SceneWorkflow(tmp_path, slug="demo_novel")
    workflow.draft(chapter_id="ch_001", scene_id="sc_001", goal="First")
    workflow.draft(chapter_id="ch_001", scene_id="sc_002", goal="Second")
    review = workflow.review(scene_id="sc_001")
    rewrite = workflow.rewrite(scene_id="sc_001")
    merged = workflow.merge(chapter_id="ch_001")
    assert review.status == "reviewed"
    assert rewrite.status == "rewritten"
    assert merged.exists()
    text = merged.read_text(encoding="utf-8")
    assert "sc_001" in text
    assert "sc_002" in text


def test_scene_cli_draft_review_rewrite_merge(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["scene", "draft", "--slug", "demo_novel", "--chapter", "ch_001", "--scene", "sc_001"]) == 0
    assert main(["scene", "review", "--slug", "demo_novel", "--scene", "sc_001"]) == 0
    assert main(["scene", "rewrite", "--slug", "demo_novel", "--scene", "sc_001"]) == 0
    assert main(["scene", "merge", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    out = capsys.readouterr().out
    assert "Scene Workflow" in out
    assert (tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md").exists()
