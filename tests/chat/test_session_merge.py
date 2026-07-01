"""Session merge tests (Task 131)."""

from __future__ import annotations

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_session_merge_only_approved_branch_messages(tmp_path):
    store = ChatSessionStore(tmp_path)
    target = store.create(mode="general_chat", session_id="session_001")
    store.append_message(target.id, "user", "base")
    branch = store.branch(target.id, from_step=1, name="alt")
    store.append_message(branch.id, "assistant", "draft maybe", provider_metadata={"status": "draft"})
    store.append_message(branch.id, "assistant", "approved ending", provider_metadata={"approved": True})

    result = store.merge(branch.id, into_id=target.id, only_approved=True)

    assert result.source_session_id == branch.id
    assert result.target_session_id == target.id
    assert result.merged_count == 1
    assert result.skipped_count == 1
    target_messages = store.load_context(target.id).messages
    assert [message.content for message in target_messages] == ["base", "approved ending"]
    assert target_messages[-1].provider_metadata["merge"]["source_session_id"] == branch.id
    assert target_messages[-1].provider_metadata["merge"]["source_step"] == 3
    assert [message.content for message in store.load_context(branch.id).messages] == [
        "base",
        "draft maybe",
        "approved ending",
    ]


def test_session_merge_can_select_message_steps(tmp_path):
    store = ChatSessionStore(tmp_path)
    target = store.create(mode="project_chat", project_slug="demo", session_id="session_001")
    store.append_message(target.id, "user", "base")
    branch = store.branch(target.id, from_step=1, name="alt")
    store.append_message(branch.id, "assistant", "first branch")
    store.append_message(branch.id, "assistant", "second branch")

    result = store.merge(branch.id, into_id=target.id, message_steps=[2])

    assert result.merged_count == 1
    assert [message.content for message in store.load_context(target.id).messages] == ["base", "first branch"]


def test_session_merge_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(".pf-agent")
    target = store.create(mode="general_chat", session_id="session_001")
    store.append_message(target.id, "user", "base")
    branch = store.branch(target.id, from_step=1, name="alt")
    store.append_message(branch.id, "assistant", "approved ending", provider_metadata={"approved": True})

    assert main(["session", "merge", branch.id, "--into", target.id, "--only-approved"]) == 0

    out = capsys.readouterr().out
    assert "Session Merge" in out
    assert "approved ending" in [message.content for message in store.load_context(target.id).messages]
