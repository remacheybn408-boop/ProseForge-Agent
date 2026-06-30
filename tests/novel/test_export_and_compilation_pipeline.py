"""Export and compilation pipeline tests (Task 86)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import BookExporter, NovelProjectStore


def _seed_book(root):
    NovelProjectStore(root).init_project(slug="demo_novel", title="Demo Novel", author="Writer")
    project = root / "projects" / "demo_novel"
    chapters = project / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "ch_001.md").write_text("# Chapter One\nOne body\n", encoding="utf-8")
    (chapters / "ch_002.md").write_text("# Chapter Two\nTwo body\n", encoding="utf-8")
    manifest_path = project / "project.manifest.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    payload["structure"]["chapters"] = [
        {"id": "ch_001", "title": "Chapter One", "path": str(chapters / "ch_001.md")},
        {"id": "ch_002", "title": "Chapter Two", "path": str(chapters / "ch_002.md")},
    ]
    manifest_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_export_and_compilation_pipeline_contract(tmp_path):
    _seed_book(tmp_path)
    result = BookExporter(tmp_path, slug="demo_novel").export(format="txt")
    text = result.path.read_text(encoding="utf-8")
    assert result.status == "ok"
    assert result.path.name == "demo_novel.txt"
    assert "Demo Novel" in text
    assert "Copyright" in text
    assert "Table of Contents" in text
    assert "Chapter One" in text
    assert "Chapter Two" in text


def test_export_markdown_has_front_and_back_matter(tmp_path):
    _seed_book(tmp_path)
    result = BookExporter(tmp_path, slug="demo_novel").export(format="markdown", back_matter="THE END")
    text = result.path.read_text(encoding="utf-8")
    assert result.path.suffix == ".md"
    assert "# Demo Novel" in text
    assert "THE END" in text


def test_export_chapter_range(tmp_path):
    _seed_book(tmp_path)
    result = BookExporter(tmp_path, slug="demo_novel").export(format="txt", chapter_range=("ch_002", "ch_002"))
    text = result.path.read_text(encoding="utf-8")
    assert "Chapter Two" in text
    assert "One body" not in text


def test_export_cli_generates_book_artifact(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _seed_book(tmp_path / ".pf-agent" / "workspace")
    assert main(["export", "--slug", "demo_novel", "--format", "txt"]) == 0
    out = capsys.readouterr().out
    assert "Book Export" in out
    assert (tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "exports" / "demo_novel.txt").exists()
