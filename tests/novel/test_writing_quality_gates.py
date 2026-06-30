"""Writing quality gate tests (Task 98)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, StyleProfileCompiler, WritingQualityGateRunner


def test_writing_quality_gates_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    StyleProfileCompiler(tmp_path, slug="demo_novel").compile(["zero quotation marks", "low dialogue"])
    runner = WritingQualityGateRunner(tmp_path, slug="demo_novel")

    result = runner.check_text(
        'I saw the door.\n"Hello." "No." "Yes."\nShe felt sad and the door was opened.',
        chapter="ch_001",
    )

    codes = {violation["code"] for violation in result["violations"]}
    assert {"pov_consistency", "no_quotes", "dialogue_ratio", "show_dont_tell", "passive_narration"} <= codes
    assert all(violation["line"] >= 1 for violation in result["violations"])
    assert all(violation["column"] >= 1 for violation in result["violations"])
    assert all(violation["suggestion"] for violation in result["violations"])


def test_writing_quality_report_summarizes_saved_checks(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    runner = WritingQualityGateRunner(tmp_path, slug="demo_novel")
    runner.check_text("She felt afraid.", chapter="ch_001")

    report = runner.report()

    assert report["chapters"][0]["chapter"] == "ch_001"
    assert report["summary"]["total_violations"] == 1


def test_quality_cli_check_and_report(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["style", "compile", "--slug", "demo_novel", "--preference", "zero quotation marks"]) == 0
    chapter_path = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter_path.parent.mkdir(parents=True)
    chapter_path.write_text('"Hello."', encoding="utf-8")

    assert main(["quality", "check", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    assert main(["quality", "report", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Quality Check" in out
    assert "Quality Report" in out
    assert "no_quotes" in out
