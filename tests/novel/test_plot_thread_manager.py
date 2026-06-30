"""Plot thread manager tests (Task 91)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, PlotThreadManager


def test_plot_thread_manager_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    manager = PlotThreadManager(tmp_path, slug="demo_novel")
    thread = manager.add_thread(
        id="thread_main",
        type="main",
        status="active",
        first_appearance="ch_001",
        last_touched="ch_002",
        expected_payoff="ch_010",
        linked_chapters=["ch_001", "ch_002"],
        linked_characters=["Lin"],
    )

    assert thread.id == "thread_main"
    assert manager.list()[0].expected_payoff == "ch_010"

    stale = manager.stale(current_chapter=8, max_gap=3)
    assert stale[0]["id"] == "thread_main"
    assert stale[0]["chapters_since_touched"] == 6


def test_plot_thread_manager_ignores_resolved_threads_for_stale(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    manager = PlotThreadManager(tmp_path, slug="demo_novel")
    manager.add_thread(
        id="thread_resolved",
        type="subplot",
        status="resolved",
        first_appearance="ch_001",
        last_touched="ch_001",
        expected_payoff="ch_003",
    )

    assert manager.stale(current_chapter=9, max_gap=2) == []


def test_plot_thread_cli_add_list_stale(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    assert (
        main(
            [
                "plot-thread",
                "add",
                "--slug",
                "demo_novel",
                "--id",
                "thread_main",
                "--type",
                "main",
                "--status",
                "active",
                "--first-appearance",
                "ch_001",
                "--last-touched",
                "ch_002",
                "--expected-payoff",
                "ch_010",
                "--linked-chapter",
                "ch_001",
                "--linked-character",
                "Lin",
            ]
        )
        == 0
    )
    assert main(["plot-thread", "list", "--slug", "demo_novel"]) == 0
    assert main(["plot-thread", "stale", "--slug", "demo_novel", "--current-chapter", "8", "--max-gap", "3"]) == 0
    out = capsys.readouterr().out
    assert "Plot Thread" in out
    assert "thread_main" in out
    assert "stale" in out
