"""Bulk manuscript import tests (Task 83)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import BulkImporter, NovelProjectStore


def test_bulk_import_contract(tmp_path):
    source = tmp_path / "novel.txt"
    source.write_text("# 第一章 开端\n第一章正文\n\n# 第二章 转折\n第二章正文\n", encoding="utf-8")
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    result = BulkImporter(tmp_path, slug="demo_novel").import_manuscript(source)
    manifest = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8"))
    assert result.status == "ok"
    assert [chapter.id for chapter in result.chapters] == ["ch_001", "ch_002"]
    assert (tmp_path / "projects" / "demo_novel" / "chapters" / "ch_001.md").exists()
    assert manifest["structure"]["chapters"][0]["title"] == "第一章 开端"
    assert result.raw_artifact_id.startswith("raw_import_")


def test_import_preview_does_not_write_manifest(tmp_path):
    source = tmp_path / "novel.md"
    source.write_text("## Chapter One\nBody\n## Chapter Two\nBody\n", encoding="utf-8")
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    before = (tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8")
    preview = BulkImporter(tmp_path, slug="demo_novel").preview(source)
    after = (tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8")
    assert len(preview.chapters) == 2
    assert before == after


def test_import_writes_split_chapter_content(tmp_path):
    source = tmp_path / "novel.txt"
    source.write_text("# Chapter One\nOne body\n\n# Chapter Two\nTwo body\n", encoding="utf-8")
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    BulkImporter(tmp_path, slug="demo_novel").import_manuscript(source)
    ch_001 = (tmp_path / "projects" / "demo_novel" / "chapters" / "ch_001.md").read_text(encoding="utf-8")
    ch_002 = (tmp_path / "projects" / "demo_novel" / "chapters" / "ch_002.md").read_text(encoding="utf-8")
    assert "One body" in ch_001
    assert "Two body" not in ch_001
    assert "Two body" in ch_002


def test_folder_import_sorts_chapter_files(tmp_path):
    folder = tmp_path / "chapters"
    folder.mkdir()
    (folder / "02.md").write_text("# 第二章\nTwo", encoding="utf-8")
    (folder / "01.md").write_text("# 第一章\nOne", encoding="utf-8")
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    result = BulkImporter(tmp_path, slug="demo_novel").import_manuscript(folder)
    assert [chapter.title for chapter in result.chapters] == ["第一章", "第二章"]


def test_bulk_import_cli_preview_and_import(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "novel.txt"
    source.write_text("# Chapter One\nBody\n", encoding="utf-8")
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["import", "preview", str(source), "--slug", "demo_novel"]) == 0
    assert main(["import", "manuscript", str(source), "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Import Preview" in out
    assert "Bulk Import" in out
    assert (tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md").exists()
