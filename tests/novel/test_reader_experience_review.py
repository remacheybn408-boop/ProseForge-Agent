"""Reader experience review tests (Task 101)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, ReaderExperienceReviewer


READER_SIGNAL_NAMES = {
    "pacing",
    "info_density",
    "suspense",
    "payoff",
    "oppression",
    "fatigue",
    "confusion",
    "emotion_curve",
    "chapter_hook",
}


def _seed_chapter(root, slug, chapter, text):
    path = root / "projects" / slug / "chapters" / f"{chapter}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_reader_experience_review_contract(tmp_path):
    """A chapter review returns a structured reader report with actionable suggestions."""
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed_chapter(tmp_path, "demo_novel", "ch_001", "林决定离开。走廊很安静。他等待黎明。一切都结束了。")
    reviewer = ReaderExperienceReviewer(tmp_path, slug="demo_novel")

    report = reviewer.review(chapter="ch_001")

    assert {signal.name for signal in report.signals} >= READER_SIGNAL_NAMES
    assert report.target == "ch_001"
    assert report.scope == "chapter"
    assert report.suggestions  # actionable revision suggestions
    assert report.path.exists()
    data = report.to_dict()
    assert data["signals"] and data["suggestions"]
    assert data["path"] == str(report.path)


def test_reader_review_requires_exactly_one_target(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    reviewer = ReaderExperienceReviewer(tmp_path, slug="demo_novel")

    for kwargs in ({}, {"chapter": "ch_001", "volume": "vol_001"}):
        try:
            reviewer.review(**kwargs)
        except ValueError as exc:
            assert "chapter" in str(exc) or "volume" in str(exc)
        else:
            raise AssertionError("review must require exactly one of chapter/volume")


def test_reader_review_missing_chapter_raises(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    reviewer = ReaderExperienceReviewer(tmp_path, slug="demo_novel")

    try:
        reviewer.review(chapter="ch_404")
    except ValueError as exc:
        assert "ch_404" in str(exc)
    else:
        raise AssertionError("missing chapter should fail")


def test_reader_review_volume_aggregates_chapters(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    _seed_chapter(tmp_path, "demo_novel", "ch_001", "他握紧了拳头。但是门突然打开了。")
    _seed_chapter(tmp_path, "demo_novel", "ch_002", "她笑了。胜利属于他们。一切都结束了。")
    reviewer = ReaderExperienceReviewer(tmp_path, slug="demo_novel")

    report = reviewer.review(volume="vol_001")

    assert report.scope == "volume"
    assert report.target == "vol_001"
    assert {signal.name for signal in report.signals} >= READER_SIGNAL_NAMES
    assert report.path.exists()


def test_reader_review_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    chapter = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("林决定离开。走廊很安静。一切都结束了。", encoding="utf-8")

    assert main(["reader-review", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    out = capsys.readouterr().out
    assert "Reader Experience" in out
