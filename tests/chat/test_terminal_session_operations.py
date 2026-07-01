"""Terminal session operation tests (Task 154)."""

from __future__ import annotations

import pytest

from proseforge_agent.chat import ChatSessionStore
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError


def test_undo_soft_deletes_last_turn(tmp_path):
    store = ChatSessionStore(tmp_path / ".pf-agent")
    session = store.create(session_id="session_001", mode="general_chat")
    store.append_message(session.id, "user", "hello")
    store.append_message(session.id, "assistant", "world")

    result = store.rewind(session.id, steps=1, reason="undo")

    context = store.load_context(session.id)
    marker = context.messages[-1]
    assert result.soft_deleted_steps == [2]
    assert marker.role == "system"
    assert marker.provider_metadata["operation"] == "rewind"
    assert marker.provider_metadata["soft_deleted_steps"] == [2]
    assert context.messages[1].content == "world"


def test_compress_appends_summary_with_source_refs(tmp_path):
    store = ChatSessionStore(tmp_path / ".pf-agent")
    session = store.create(session_id="session_001", mode="general_chat")
    store.append_message(session.id, "user", "first")
    store.append_message(session.id, "assistant", "second")

    result = store.compress(session.id, upto_step=2)

    marker = store.load_context(session.id).messages[-1]
    assert result.source_steps == [1, 2]
    assert marker.provider_metadata["operation"] == "compress"
    assert marker.evidence_refs == ["session:session_001:step:1", "session:session_001:step:2"]


def test_usage_and_resume_are_read_only(tmp_path):
    store = ChatSessionStore(tmp_path / ".pf-agent")
    session = store.create(session_id="session_001", mode="general_chat")
    store.append_message(session.id, "user", "hello world")

    usage = store.usage(session.id)
    resumed = store.resume(session.id)

    assert usage.message_count == 1
    assert usage.word_count == 2
    assert resumed.id == session.id
    with pytest.raises(ConfigurationError):
        store.resume("missing")


def test_chat_usage_slash_command_uses_session_operations(capsys):
    assert main(["chat", "--message", "/usage", "--provider", "fake", "--no-project"]) == 0

    out = capsys.readouterr().out
    assert "Session Usage" in out
    assert "messages=" in out
