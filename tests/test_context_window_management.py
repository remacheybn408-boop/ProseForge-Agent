"""Context window management tests (Task 111)."""

from __future__ import annotations

from proseforge_agent.agent.context_window import ContextWindowManager
from proseforge_agent.chat import ChatSessionStore
from proseforge_agent.llm import Message
from proseforge_agent.cli import main


def test_context_window_manager_reports_usage_and_truncates_evidence():
    manager = ContextWindowManager(provider_limits={"fake": 40})
    report = manager.status(
        provider="fake",
        messages=[Message(role="user", content="hello " * 10)],
        evidence=[
            {"id": "e1", "text": "canon " * 25},
            {"id": "e2", "text": "short note"},
        ],
        reserve_tokens=10,
    )

    assert report.provider == "fake"
    assert report.max_context_tokens == 40
    assert report.prompt_tokens > 0
    assert report.evidence_budget_tokens == 20
    assert report.truncated_evidence_ids == ["e1"]
    assert report.remaining_tokens >= 0


def test_compact_messages_summarizes_early_conversation():
    manager = ContextWindowManager()
    messages = [
        Message(role="user", content="first"),
        Message(role="assistant", content="second"),
        Message(role="user", content="third"),
        Message(role="assistant", content="fourth"),
    ]

    compacted = manager.compact_messages(messages, keep_last=2)

    assert compacted[0].role == "system"
    assert "summary" in compacted[0].content
    assert [message.content for message in compacted[1:]] == ["third", "fourth"]


def test_context_cli_status_and_compact(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(tmp_path / ".pf-agent")
    session = store.create(mode="general_chat", session_id="session_001")
    store.append_message(session.id, "user", "first")
    store.append_message(session.id, "assistant", "second")
    store.append_message(session.id, "user", "third")

    assert main(["context", "status", "--provider", "fake", "--max-context", "40"]) == 0
    assert main(["context", "compact", "--session", "session_001", "--keep-last", "1"]) == 0

    out = capsys.readouterr().out
    assert "Context Window" in out
    assert "remaining_tokens" in out
    assert "compacted_messages=2" in out
