"""Multi-context switch tests (Task 132)."""

from __future__ import annotations

import yaml

from proseforge_agent.chat.context import ActiveContextStore
from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_active_context_switches_project_and_session(tmp_path):
    store = ActiveContextStore(tmp_path)

    project_context = store.switch(project="demo_novel")
    session_context = store.switch(session="session_001")

    assert project_context.project == "demo_novel"
    assert session_context.project == "demo_novel"
    assert session_context.session == "session_001"
    payload = yaml.safe_load((tmp_path / "active_context.yaml").read_text(encoding="utf-8"))
    assert payload["active_context"] == {
        "project": "demo_novel",
        "session": "session_001",
        "pinned_sessions": [],
    }


def test_active_context_pins_sessions_without_duplicates(tmp_path):
    store = ActiveContextStore(tmp_path)

    first = store.pin(session="session_001")
    second = store.pin(session="session_001")

    assert first.pinned_sessions == ["session_001"]
    assert second.pinned_sessions == ["session_001"]


def test_context_switch_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session_store = ChatSessionStore(".pf-agent")
    session_store.create(mode="project_chat", project_slug="demo_novel", session_id="session_001")

    assert main(["context", "switch", "--project", "demo_novel"]) == 0
    assert main(["context", "switch", "--session", "session_001"]) == 0
    assert main(["context", "pin", "--session", "session_001"]) == 0
    assert main(["context", "current"]) == 0

    out = capsys.readouterr().out
    assert "Active Context" in out
    assert "demo_novel" in out
    assert "session_001" in out
