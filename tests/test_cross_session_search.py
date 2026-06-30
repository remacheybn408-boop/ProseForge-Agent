"""Cross-session search tests (Task 128)."""

from __future__ import annotations

from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.cli import main


def test_cross_session_search_finds_messages_tools_and_evidence(tmp_path):
    store = ChatSessionStore(tmp_path)
    demo = store.create(mode="project_chat", project_slug="demo", session_id="demo_session")
    other = store.create(mode="general_chat", project_slug="other", session_id="other_session")
    store.append_message(demo.id, "user", "DeepSeek provider key fails")
    store.append_message(
        demo.id,
        "assistant",
        "checked evidence",
        evidence_refs=["ev_deepseek"],
        tool_calls=[{"name": "provider.fallback", "decision": "DeepSeek -> fake"}],
    )
    store.append_message(other.id, "user", "DeepSeek unrelated")

    results = store.search("DeepSeek", project_slug="demo")

    assert {result.kind for result in results} == {"evidence", "message", "tool_call"}
    assert all(result.session_id == "demo_session" for result in results)
    assert any("provider key" in result.snippet for result in results)


def test_cross_session_search_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = ChatSessionStore(".pf-agent")
    session = store.create(mode="project_chat", project_slug="demo", session_id="session_001")
    store.append_message(session.id, "user", "第3章 DeepSeek diagnostics")

    assert main(["session", "search", "DeepSeek", "--project", "demo"]) == 0

    out = capsys.readouterr().out
    assert "Conversation Search" in out
    assert "session_001" in out
    assert "DeepSeek" in out
