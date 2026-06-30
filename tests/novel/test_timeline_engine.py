"""Timeline engine tests (Task 90)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, TimelineEngine


def test_timeline_engine_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    timeline = TimelineEngine(tmp_path, slug="demo_novel")
    timeline.add_event(
        id="evt_001",
        title="Lin at harbor",
        story_day=1,
        order=1,
        characters=["Lin"],
        location="Harbor",
    )
    timeline.add_event(
        id="evt_002",
        title="Lin at palace",
        story_day=1,
        order=1,
        characters=["Lin"],
        location="Palace",
        parallel=True,
    )
    conflicts = timeline.check()
    assert conflicts[0]["type"] == "character_location"
    assert conflicts[0]["character"] == "Lin"
    assert set(conflicts[0]["locations"]) == {"Harbor", "Palace"}


def test_timeline_view_sorts_by_story_day_and_order(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    timeline = TimelineEngine(tmp_path, slug="demo_novel")
    timeline.add_event(id="evt_002", title="Second", story_day=2, order=1)
    timeline.add_event(id="evt_001", title="First", story_day=1, order=2)
    assert [event.id for event in timeline.view()] == ["evt_001", "evt_002"]


def test_timeline_cli_add_check_view(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert main(["timeline", "add-event", "--slug", "demo_novel", "--id", "evt_001", "--title", "Lin Harbor", "--story-day", "1", "--order", "1", "--character", "Lin", "--location", "Harbor"]) == 0
    assert main(["timeline", "add-event", "--slug", "demo_novel", "--id", "evt_002", "--title", "Lin Palace", "--story-day", "1", "--order", "1", "--character", "Lin", "--location", "Palace", "--parallel"]) == 0
    assert main(["timeline", "check", "--slug", "demo_novel"]) == 0
    assert main(["timeline", "view", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Timeline" in out
    assert "character_location" in out
