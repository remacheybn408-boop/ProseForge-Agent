"""Audit trail and debuggability tests (Task 115)."""

from __future__ import annotations

import json

from proseforge_agent.agent.audit import AuditTrailStore
from proseforge_agent.cli import main


def test_audit_trail_records_redacted_turn_and_exports(tmp_path):
    store = AuditTrailStore(tmp_path)

    step = store.record_turn(
        "session_001",
        {
            "input": "draft with api_key=sk-secret",
            "intent": {"name": "draft_note"},
            "system_prompt_version": "professional_novel_editor@1",
            "evidence_pack": [{"id": "ev1", "text": "canon"}],
            "tool_choice": "draft.note",
            "tool_args": {"api_key": "sk-secret", "text": "hello"},
            "tool_result": {"status": "ok", "secret_token": "tok-secret"},
            "provider": {"name": "fake", "model": "fake"},
            "latency_ms": 3,
            "token_usage": {"prompt_tokens": 2, "completion_tokens": 1},
            "model_output": "done",
            "final_action": "respond",
            "trace_id": "trace-001",
        },
    )

    assert step.step == 1
    assert step.tool_args["api_key"] == "[redacted]"
    serialized = (tmp_path / "audit" / "session_001.jsonl").read_text(encoding="utf-8")
    assert "sk-secret" not in serialized
    assert "tok-secret" not in serialized

    exported_json = store.export_json("session_001")
    assert json.loads(exported_json)[0]["trace_id"] == "trace-001"
    exported_md = store.export_markdown("session_001")
    assert "## Step 1" in exported_md
    assert "draft_note" in exported_md


def test_audit_trail_replay_returns_ordered_steps(tmp_path):
    store = AuditTrailStore(tmp_path)
    store.record_turn("session_001", {"input": "hello", "intent": {"name": "answer_directly"}, "model_output": "hi"})
    store.record_turn("session_001", {"input": "again", "intent": {"name": "answer_directly"}, "model_output": "bye"})

    replay = store.replay("session_001")

    assert replay.session_id == "session_001"
    assert replay.step_count == 2
    assert replay.final_output == "bye"


def test_debug_cli_session_step_replay(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = AuditTrailStore(".pf-agent")
    store.record_turn("session_001", {"input": "hello", "intent": {"name": "answer_directly"}, "model_output": "hi"})

    assert main(["debug", "session", "session_001"]) == 0
    assert main(["debug", "step", "session_001", "--step", "1"]) == 0
    assert main(["debug", "replay", "session_001"]) == 0

    out = capsys.readouterr().out
    assert "Audit Session" in out
    assert "Audit Step" in out
    assert "Audit Replay" in out


def test_chat_cli_writes_audit_step(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["chat", "--message", "hello", "--provider", "fake"]) == 0

    rows = (tmp_path / ".pf-agent" / "audit" / "cli.jsonl").read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    assert payload["input"] == "hello"
    assert payload["provider"]["name"] == "fake"
    assert payload["final_action"] == "respond"
