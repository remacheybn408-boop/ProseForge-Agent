"""Conversation lifecycle tests (Task 127)."""

from __future__ import annotations

import json

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_conversation_lifecycle_status_transitions(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="general_chat", session_id="session_001")

    assert session.status == "active"
    assert store.archive("session_001").status == "archived"
    assert store.restore("session_001").status == "active"
    assert store.pin("session_001").status == "pinned"
    assert store.delete("session_001").status == "deleted"
    assert store.list() == []
    assert store.list(include_deleted=True)[0].status == "deleted"


def test_conversation_cleanup_soft_deletes_old_unpinned_sessions(tmp_path):
    store = ChatSessionStore(tmp_path)
    old = store.create(mode="general_chat", session_id="old")
    pinned = store.create(mode="general_chat", session_id="pinned")
    store.pin("pinned")

    for session in (old, pinned):
        path = tmp_path / "chats" / session.id / "session.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["updated_at"] = "2000-01-01T00:00:00+00:00"
        path.write_text(json.dumps(payload), encoding="utf-8")

    cleaned = store.cleanup(older_than_days=90)

    assert [session.id for session in cleaned] == ["old"]
    assert store.load_context("old").session.status == "deleted"
    assert store.load_context("pinned").session.status == "pinned"


def test_session_lifecycle_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(".pf-agent")
    store.create(mode="general_chat", session_id="session_001")

    assert main(["session", "list"]) == 0
    assert main(["session", "show", "session_001"]) == 0
    assert main(["session", "archive", "session_001"]) == 0
    assert main(["session", "restore", "session_001"]) == 0
    assert main(["session", "delete", "session_001"]) == 0
    assert main(["session", "cleanup", "--older-than", "90d"]) == 0

    out = capsys.readouterr().out
    assert "Conversation Sessions" in out
    assert "session_001" in out
    assert "deleted" in out
