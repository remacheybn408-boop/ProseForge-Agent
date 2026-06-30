"""Tone and style profile compiler tests (Task 97)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, StyleProfileCompiler, WritingRulesStore


def test_tone_and_style_profile_compiler_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    compiler = StyleProfileCompiler(tmp_path, slug="demo_novel")

    profile = compiler.compile(
        [
            "zero quotation marks",
            "low dialogue",
            "no em dash",
            "few adjectives",
            "show-don't-tell",
        ]
    )

    assert "no_quotes" in profile.punctuation_checks
    assert "no_em_dash" in profile.punctuation_checks
    assert profile.dialogue_ratio["max"] == 0.35
    assert "show_dont_tell" in profile.narration_distance_checks
    assert "few adjectives" in profile.style_prompt_fragment

    result = compiler.check_text(
        '"Hello." "No." "Yes." The room is very bright \u2014 too bright.',
        chapter="ch_001",
    )
    codes = {violation["code"] for violation in result["violations"]}
    assert {"no_quotes", "no_em_dash", "dialogue_ratio"} <= codes


def test_style_compile_reads_explicit_writing_rules(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    WritingRulesStore(tmp_path, slug="demo_novel").add("zero quotation marks", level="project")

    profile = StyleProfileCompiler(tmp_path, slug="demo_novel").compile_from_rules()

    assert profile.review_gate_rules == ["no_quotes"]


def test_style_cli_compile_and_check(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["rules", "add", "zero quotation marks", "--slug", "demo_novel"]) == 0
    assert main(["rules", "add", "low dialogue", "--slug", "demo_novel"]) == 0
    chapter_path = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter_path.parent.mkdir(parents=True)
    chapter_path.write_text('"Hello." "No." "Yes."', encoding="utf-8")

    assert main(["style", "compile", "--slug", "demo_novel"]) == 0
    assert main(["style", "check", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    out = capsys.readouterr().out
    assert "Style Profile" in out
    assert "Style Check" in out
    assert "no_quotes" in out
