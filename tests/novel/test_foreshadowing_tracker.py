"""Foreshadowing tracker tests (Task 92)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import ForeshadowingTracker, NovelProjectStore


def test_foreshadowing_tracker_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    tracker = ForeshadowingTracker(tmp_path, slug="demo_novel")
    tracker.add(
        id="foreshadow_001",
        planted_chapter="ch_001",
        expected_payoff_chapter="ch_005",
        status="planted",
        importance="high",
        related_characters=["Lin"],
        related_plot_thread="thread_main",
    )

    overdue = tracker.overdue(current_chapter=8, max_gap=3)
    assert overdue[0]["id"] == "foreshadow_001"
    assert overdue[0]["chapters_since_planted"] == 7
    assert overdue[0]["expected_payoff_chapter"] == "ch_005"

    resolved = tracker.resolve("foreshadow_001", resolved_chapter="ch_008")
    assert resolved["status"] == "resolved"
    assert tracker.overdue(current_chapter=9, max_gap=3) == []


def test_foreshadowing_tracker_uses_expected_payoff_as_overdue_signal(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    tracker = ForeshadowingTracker(tmp_path, slug="demo_novel")
    tracker.add(
        id="foreshadow_002",
        planted_chapter="ch_001",
        expected_payoff_chapter="ch_003",
        status="developing",
    )

    overdue = tracker.overdue(current_chapter=4, max_gap=99)
    assert overdue[0]["reason"] == "past_expected_payoff"


def test_foreshadowing_cli_add_list_overdue_resolve(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert (
        main(
            [
                "foreshadow",
                "add",
                "--slug",
                "demo_novel",
                "--id",
                "foreshadow_001",
                "--planted-chapter",
                "ch_001",
                "--expected-payoff-chapter",
                "ch_005",
                "--status",
                "planted",
                "--importance",
                "high",
                "--related-character",
                "Lin",
                "--related-plot-thread",
                "thread_main",
            ]
        )
        == 0
    )
    assert main(["foreshadow", "list", "--slug", "demo_novel"]) == 0
    assert main(["foreshadow", "overdue", "--slug", "demo_novel", "--current-chapter", "8", "--max-gap", "3"]) == 0
    assert main(["foreshadow", "resolve", "--slug", "demo_novel", "--id", "foreshadow_001", "--resolved-chapter", "ch_008"]) == 0
    out = capsys.readouterr().out
    assert "Foreshadow" in out
    assert "foreshadow_001" in out
    assert "overdue" in out
