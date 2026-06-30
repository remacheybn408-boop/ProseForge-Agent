"""Writing analytics tests (Task 107)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, WritingAnalytics


def _seed(tmp_path, slug="demo_novel"):
    NovelProjectStore(tmp_path).init_project(slug=slug)
    chapters = tmp_path / "projects" / slug / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    return chapters


def test_writing_analytics_contract(tmp_path):
    """Analytics produce a daily word trend, a completion prediction, and CSV output."""
    chapters = _seed(tmp_path)
    (chapters / "ch_001.md").write_text("一二三四五", encoding="utf-8")
    analytics = WritingAnalytics(tmp_path, slug="demo_novel")
    analytics.record("2026-06-28", chapter="ch_001", words=1200, revisions=1, provider_cost=0.5, minutes=60)
    analytics.record("2026-06-29", chapter="ch_001", words=800, revisions=2, provider_cost=0.3, minutes=40)

    daily = analytics.daily()
    assert [stat.date for stat in daily] == ["2026-06-28", "2026-06-29"]
    assert daily[0].words == 1200

    summary = analytics.summary(target_words=10000)
    assert summary.total_words == 2000
    assert summary.avg_daily_words == 1000
    assert summary.days_remaining == 8  # ceil((10000-2000)/1000)

    csv_text = analytics.export_csv()
    header = csv_text.splitlines()[0]
    assert header.startswith("date,words,revisions")
    assert "2026-06-28" in csv_text


def test_chapter_words_counts_files(tmp_path):
    chapters = _seed(tmp_path)
    (chapters / "ch_001.md").write_text("一二三", encoding="utf-8")
    (chapters / "ch_002.md").write_text("四五六七", encoding="utf-8")
    analytics = WritingAnalytics(tmp_path, slug="demo_novel")

    words = analytics.chapter_words()

    assert words["ch_001"] == 3
    assert words["ch_002"] == 4


def test_summary_without_target_has_no_prediction(tmp_path):
    _seed(tmp_path)
    analytics = WritingAnalytics(tmp_path, slug="demo_novel")
    analytics.record("2026-06-28", chapter="ch_001", words=500)

    summary = analytics.summary()

    assert summary.days_remaining is None


def test_record_persists_across_instances(tmp_path):
    _seed(tmp_path)
    WritingAnalytics(tmp_path, slug="demo_novel").record("2026-06-28", chapter="ch_001", words=300)

    daily = WritingAnalytics(tmp_path, slug="demo_novel").daily()

    assert daily[0].words == 300


def test_stats_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    analytics = WritingAnalytics(tmp_path / ".pf-agent" / "workspace", slug="demo_novel")
    analytics.record("2026-06-28", chapter="ch_001", words=1000)
    analytics.record("2026-06-29", chapter="ch_001", words=1000)

    assert main(["stats", "--slug", "demo_novel"]) == 0
    assert "Writing Analytics" in capsys.readouterr().out

    assert main(["stats", "daily", "--slug", "demo_novel"]) == 0
    assert "2026-06-28" in capsys.readouterr().out

    assert main(["stats", "export", "--slug", "demo_novel", "--format", "csv"]) == 0
    assert "date,words,revisions" in capsys.readouterr().out
