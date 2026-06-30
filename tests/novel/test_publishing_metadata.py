"""Publishing metadata tests (Task 87)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import BookExporter, NovelProjectStore, PublishingMetadataStore


def test_publishing_metadata_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel", title="Demo Novel", author="Writer")
    store = PublishingMetadataStore(tmp_path, slug="demo_novel")
    metadata = store.init(
        title="Demo Novel",
        subtitle="A Test Book",
        author="Writer",
        pen_name="Pen",
        summary="A short summary",
        keywords=["fantasy", "test"],
        copyright="Copyright 2026 Writer",
        ai_usage_statement="AI assisted editing used.",
        platform_profiles={"kindle": {"category": "Fantasy"}},
    )
    assert metadata.path.name == "publishing.yaml"
    assert metadata.data["title"] == "Demo Novel"
    assert metadata.data["keywords"] == ["fantasy", "test"]
    assert store.validate()["status"] == "ok"


def test_publishing_edit_updates_existing_metadata(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = PublishingMetadataStore(tmp_path, slug="demo_novel")
    store.init(title="Old", author="A")
    updated = store.edit(summary="New summary", keywords=["new"])
    assert updated.data["summary"] == "New summary"
    assert updated.data["keywords"] == ["new"]


def test_export_includes_publishing_metadata(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel", title="Demo Novel")
    project = tmp_path / "projects" / "demo_novel"
    chapters = project / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "ch_001.md").write_text("# Chapter One\nBody\n", encoding="utf-8")
    PublishingMetadataStore(tmp_path, slug="demo_novel").init(
        title="Demo Novel",
        author="Writer",
        copyright="Copyright 2026 Writer",
        ai_usage_statement="AI assisted editing used.",
    )
    result = BookExporter(tmp_path, slug="demo_novel").export(format="txt")
    text = result.path.read_text(encoding="utf-8")
    assert "Copyright 2026 Writer" in text
    assert "AI assisted editing used." in text


def test_publishing_cli_init_edit_validate(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["publishing", "init", "--slug", "demo_novel", "--title", "Demo Novel", "--author", "Writer"]) == 0
    assert main(["publishing", "edit", "--slug", "demo_novel", "--summary", "Summary"]) == 0
    assert main(["publishing", "validate", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Publishing Metadata" in out
    assert (tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "publishing.yaml").exists()
