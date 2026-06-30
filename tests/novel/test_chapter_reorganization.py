"""Chapter reorganization tests (Task 85)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import ChapterReorganizer, NovelProjectStore


def _seed_manifest(root):
    NovelProjectStore(root).init_project(slug="demo_novel")
    path = root / "projects" / "demo_novel" / "project.manifest.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["structure"]["volumes"] = [{"id": "vol_001"}, {"id": "vol_002"}]
    payload["structure"]["chapters"] = [
        {"id": "ch_001", "title": "One", "volume_id": "vol_001"},
        {"id": "ch_002", "title": "Two", "volume_id": "vol_001"},
        {"id": "ch_003", "title": "Three", "volume_id": "vol_001"},
    ]
    payload["structure"]["scenes"] = [
        {"id": "sc_004_01", "chapter_id": "ch_004"},
        {"id": "sc_004_03", "chapter_id": "ch_004"},
    ]
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_chapter_reorganization_contract(tmp_path):
    _seed_manifest(tmp_path)
    result = ChapterReorganizer(tmp_path, slug="demo_novel").move(
        "ch_003",
        to_volume="vol_002",
        after="ch_001",
    )
    payload = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8"))
    assert result["status"] == "ok"
    assert [chapter["id"] for chapter in payload["structure"]["chapters"]] == ["ch_001", "ch_003", "ch_002"]
    assert payload["structure"]["chapters"][1]["volume_id"] == "vol_002"
    assert (tmp_path / "projects" / "demo_novel" / "reorg.log").exists()


def test_renumber_updates_chapter_ids_consistently(tmp_path):
    _seed_manifest(tmp_path)
    result = ChapterReorganizer(tmp_path, slug="demo_novel").renumber()
    payload = yaml.safe_load((tmp_path / "projects" / "demo_novel" / "project.manifest.yaml").read_text(encoding="utf-8"))
    assert result["mapping"]["ch_003"] == "ch_003"
    assert [chapter["id"] for chapter in payload["structure"]["chapters"]] == ["ch_001", "ch_002", "ch_003"]


def test_split_and_merge_record_reorg_log(tmp_path):
    _seed_manifest(tmp_path)
    reorganizer = ChapterReorganizer(tmp_path, slug="demo_novel")
    split = reorganizer.split("ch_004", at_scene="sc_004_03")
    merge = reorganizer.merge("ch_001", "ch_002", into="ch_001")
    log = (tmp_path / "projects" / "demo_novel" / "reorg.log").read_text(encoding="utf-8")
    assert split["status"] == "ok"
    assert merge["status"] == "ok"
    assert "split ch_004 at sc_004_03" in log
    assert "merge ch_001 ch_002 into ch_001" in log


def test_chapter_reorganization_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / ".pf-agent" / "workspace"
    _seed_manifest(root)
    assert main(["chapter", "move", "ch_003", "--slug", "demo_novel", "--to-volume", "vol_002", "--after", "ch_001"]) == 0
    assert main(["chapter", "renumber", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Chapter Reorganization" in out
