"""Explicit writing rules tests (Task 96)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, WritingRulesStore


def test_explicit_writing_rules_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = WritingRulesStore(tmp_path, slug="demo_novel")
    global_rule = store.add("Never use quotation marks", level="global")
    project_rule = store.add("Keep dialogue density low", level="project")
    chapter_rule = store.add("No cliffhanger breaks", level="chapter", chapter="ch_003")

    assert [rule.id for rule in store.list()] == [global_rule.id, project_rule.id, chapter_rule.id]

    evidence = store.evidence(chapter="ch_003")
    assert [item["id"] for item in evidence] == ["rule_001", "rule_002", "rule_003"]
    assert all(item["type"] == "writing_rule" for item in evidence)

    removed = store.remove("rule_002")
    assert removed["removed"] is True
    assert [rule.id for rule in store.list()] == ["rule_001", "rule_003"]


def test_writing_rules_evidence_filters_chapter_level(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    store = WritingRulesStore(tmp_path, slug="demo_novel")
    store.add("Only chapter three gets this rule", level="chapter", chapter="ch_003")

    assert store.evidence(chapter="ch_004") == []


def test_rules_cli_add_list_remove(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["rules", "add", "Never use quotation marks", "--slug", "demo_novel", "--level", "project"]) == 0
    assert main(["rules", "list", "--slug", "demo_novel"]) == 0
    assert main(["rules", "remove", "rule_001", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Writing Rules" in out
    assert "rule_001" in out
    assert "Never use quotation marks" in out
