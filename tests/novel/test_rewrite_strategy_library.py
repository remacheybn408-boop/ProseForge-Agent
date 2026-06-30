"""Rewrite strategy library tests (Task 100)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, RewriteStrategyLibrary


def test_rewrite_strategy_library_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    chapter = tmp_path / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text('"Hello." The corridor was quiet. Lin waited for dawn.', encoding="utf-8")
    library = RewriteStrategyLibrary(tmp_path, slug="demo_novel")

    names = {strategy.name for strategy in library.list_strategies()}
    assert {
        "expand",
        "condense",
        "lower_dialogue",
        "enhance_description",
        "increase_tension",
        "simplify_language",
        "yu_hua_plain_narration",
        "remove_quotes",
        "reduce_exposition",
    } <= names

    condensed = library.rewrite(strategy="condense", chapter="ch_001")
    lower_dialogue = library.rewrite(strategy="lower_dialogue", chapter="ch_001")

    assert condensed.path != lower_dialogue.path
    assert condensed.text != lower_dialogue.text
    assert condensed.path.exists()
    assert lower_dialogue.path.exists()


def test_rewrite_strategy_rejects_unknown_strategy(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    library = RewriteStrategyLibrary(tmp_path, slug="demo_novel")

    try:
        library.rewrite(strategy="make_it_weird", chapter="ch_001")
    except ValueError as exc:
        assert "unknown rewrite strategy" in str(exc)
    else:
        raise AssertionError("unknown strategy should fail")


def test_rewrite_cli_strategy_list_and_apply(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    chapter = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text('"Hello." The corridor was quiet. Lin waited for dawn.', encoding="utf-8")

    assert main(["rewrite", "strategies", "list"]) == 0
    assert main(["rewrite", "--slug", "demo_novel", "--strategy", "condense", "--chapter", "ch_001"]) == 0
    assert main(["rewrite", "--slug", "demo_novel", "--strategy", "lower_dialogue", "--chapter", "ch_001"]) == 0
    out = capsys.readouterr().out
    assert "Rewrite Strategies" in out
    assert "condense" in out
    assert "lower_dialogue" in out
