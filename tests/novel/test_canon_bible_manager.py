"""Canon bible manager tests (Task 88)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.novel import CanonBibleManager, NovelProjectStore


def test_canon_bible_manager_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    bible = CanonBibleManager(tmp_path, slug="demo_novel")
    entry = bible.add("character", {"id": "char_001", "name": "Lin", "role": "protagonist"})
    characters = bible.list("characters")
    assert entry["status"] == "ok"
    assert characters[0]["name"] == "Lin"
    assert (tmp_path / "projects" / "demo_novel" / "bible" / "characters.yaml").exists()


def test_bible_freeze_blocks_mutation_until_unfrozen(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    bible = CanonBibleManager(tmp_path, slug="demo_novel")
    bible.freeze()
    result = bible.add("character", {"id": "char_001", "name": "Lin"})
    assert result["status"] == "frozen"
    assert bible.list("characters") == []


def test_bible_snapshot_is_stable_and_referenceable(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    bible = CanonBibleManager(tmp_path, slug="demo_novel")
    bible.add("location", {"id": "loc_001", "name": "Harbor"})
    snapshot = bible.snapshot()
    assert snapshot["id"].startswith("bible_snapshot_")
    assert snapshot["path"].endswith(".yaml")
    assert "Harbor" in (tmp_path / snapshot["path"]).read_text(encoding="utf-8")


def test_bible_cli_add_list_freeze_snapshot(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["bible", "add", "character", "--slug", "demo_novel", "--id", "char_001", "--name", "Lin"]) == 0
    assert main(["bible", "list", "characters", "--slug", "demo_novel"]) == 0
    assert main(["bible", "snapshot", "--slug", "demo_novel"]) == 0
    assert main(["bible", "freeze", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Canon Bible" in out
    assert "Lin" in out
