import json
from pathlib import Path

import pytest

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.cli import main


def test_session_store_round_trips_utf8_messages(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="project_chat", project_slug="demo")
    store.append_message(session.id, role="user", content="今天写什么？")
    context = store.load_context(session.id)
    assert context.messages[-1].content == "今天写什么？"
    assert context.session.project_slug == "demo"


def test_list_sessions_filters_by_project(tmp_path):
    store = ChatSessionStore(tmp_path)
    demo = store.create(mode="project_chat", project_slug="demo")
    store.create(mode="project_chat", project_slug="other")
    assert [session.id for session in store.list(project_slug="demo")] == [demo.id]


def test_export_markdown_contains_tool_decisions(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="workflow_chat", project_slug="demo")
    store.append_message(
        session.id,
        role="assistant",
        content="accepted",
        tool_calls=[{"name": "chapter.accept", "status": "denied"}],
    )
    markdown = store.export_markdown(session.id)
    assert "chapter.accept" in markdown
    assert "denied" in markdown


def test_corrupt_message_line_is_reported_not_silently_dropped(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="general_chat")
    store.append_message(session.id, role="user", content="before")
    message_path = tmp_path / session.messages_path
    message_path.write_text(
        message_path.read_text(encoding="utf-8") + "{bad json}\n",
        encoding="utf-8",
    )
    context = store.load_context(session.id)
    assert context.messages[-1].content == "before"
    assert context.warnings
    assert "corrupt" in context.warnings[0].lower()


def test_session_paths_are_relative_to_workspace(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="general_chat")
    assert not Path(session.messages_path).is_absolute()
    assert (tmp_path / session.messages_path).exists()


def test_load_context_limits_messages_without_losing_last_user_turn(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="general_chat")
    for index in range(5):
        store.append_message(session.id, role="user", content=f"message {index}")
    context = store.load_context(session.id, limit=2)
    assert [message.content for message in context.messages] == ["message 3", "message 4"]


def test_export_json_preserves_evidence_and_provider_metadata(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="project_chat", project_slug="demo")
    store.append_message(
        session.id,
        role="assistant",
        content="answer",
        evidence_refs=["ev-1"],
        provider_metadata={"provider": "fake"},
    )
    payload = store.export_json(session.id)
    assert payload["messages"][0]["evidence_refs"] == ["ev-1"]
    assert payload["messages"][0]["provider_metadata"]["provider"] == "fake"


def test_missing_session_returns_controlled_error(tmp_path):
    with pytest.raises(ConfigurationError):
        ChatSessionStore(tmp_path).load_context("missing")


def test_fixture_session_messages_is_utf8_jsonl():
    fixture = Path(__file__).parent / "fixtures" / "chat" / "session_messages.jsonl"
    rows = [json.loads(line) for line in fixture.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["content"] == "今天写什么？"


def test_chat_sessions_cli_lists_sessions(capsys):
    code = main(["chat", "sessions", "--project", "demo"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Chat Sessions" in out
