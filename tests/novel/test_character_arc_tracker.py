"""Character arc tracker tests (Task 93)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import CharacterArcTracker, NovelProjectStore


def test_character_arc_tracker_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    tracker = CharacterArcTracker(tmp_path, slug="demo_novel")
    tracker.init_arc(
        character_id="char_001",
        desire="Find the missing city",
        fear="Being abandoned",
        flaw="Hides the truth",
        belief="Power keeps people safe",
        arc_status="seeded",
    )

    tracker.update_arc(
        character_id="char_001",
        turning_points=[{"chapter": "ch_003", "change": "chooses truth over control"}],
        relationship_changes=[{"character": "char_002", "change": "starts trusting Mira"}],
        chapter_appearances=["ch_003"],
        arc_status="turning",
    )

    report = tracker.report()
    arc = report["characters"][0]
    assert arc["character_id"] == "char_001"
    assert arc["arc_status"] == "turning"
    assert arc["turning_points"][0]["chapter"] == "ch_003"
    assert report["summary"][0] == "char_001: turning, 1 turning points, 1 appearances"


def test_character_arc_update_creates_missing_arc(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    tracker = CharacterArcTracker(tmp_path, slug="demo_novel")

    tracker.update_arc(character_id="char_002", chapter_appearances=["ch_001"], arc_status="introduced")

    arc = tracker.report()["characters"][0]
    assert arc["character_id"] == "char_002"
    assert arc["chapter_appearances"] == ["ch_001"]


def test_character_arc_cli_init_update_report(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert (
        main(
            [
                "character-arc",
                "init",
                "--slug",
                "demo_novel",
                "--character",
                "char_001",
                "--desire",
                "Find the missing city",
                "--fear",
                "Being abandoned",
                "--flaw",
                "Hides the truth",
                "--belief",
                "Power keeps people safe",
                "--arc-status",
                "seeded",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "character-arc",
                "update",
                "--slug",
                "demo_novel",
                "--character",
                "char_001",
                "--turning-point",
                "ch_003:chooses truth over control",
                "--relationship-change",
                "char_002:starts trusting Mira",
                "--chapter",
                "ch_003",
                "--arc-status",
                "turning",
            ]
        )
        == 0
    )
    assert main(["character-arc", "report", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Character Arc" in out
    assert "char_001" in out
    assert "turning" in out
