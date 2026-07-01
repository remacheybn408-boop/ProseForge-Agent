"""Session branching tests (Task 130)."""

from __future__ import annotations

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_session_branch_forks_transcript_without_mutating_original(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="general_chat", session_id="session_001")
    store.append_message(session.id, "user", "start")
    store.append_message(session.id, "assistant", "second")

    branch = store.branch(session.id, from_step=1, name="alt-ending")

    assert branch.id == "session_001_alt-ending"
    assert branch.status == "branched"
    assert branch.parent_session_id == "session_001"
    assert branch.branch_name == "alt-ending"
    assert branch.branched_from_step == 1
    assert [message.content for message in store.load_context(branch.id).messages] == ["start"]
    assert [message.content for message in store.load_context(session.id).messages] == ["start", "second"]


def test_session_branches_lists_child_sessions(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="project_chat", project_slug="demo", session_id="session_001")
    store.append_message(session.id, "user", "hello")

    branch = store.branch(session.id, from_step=1, name="alt-ending")

    assert [item.id for item in store.branches(session.id)] == [branch.id]


def test_session_branching_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(".pf-agent")
    session = store.create(mode="general_chat", session_id="session_001")
    store.append_message(session.id, "user", "start")
    store.append_message(session.id, "assistant", "second")

    assert main(["session", "branch", "session_001", "--from-step", "1", "--name", "alt-ending"]) == 0
    assert main(["session", "branches", "session_001"]) == 0
    assert main(["session", "switch", "session_001_alt-ending"]) == 0

    out = capsys.readouterr().out
    assert "Session Branch" in out
    assert "Session Branches" in out
    assert "Session Switch" in out
    assert "session_001_alt-ending" in out
