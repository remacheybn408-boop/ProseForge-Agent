"""Observer hooks and telemetry export tests (Task 181)."""

from __future__ import annotations

import json

from proseforge_agent.agent.observability import (
    OBSERVER_SCHEMA_VERSION,
    ObserverEvent,
    ObserverRegistry,
    TelemetryStore,
)
from proseforge_agent.cli import main


def test_observer_hook_receives_sanitized_tool_call_payload(tmp_path):
    registry = ObserverRegistry()
    captured: list[ObserverEvent] = []
    registry.register(captured.append)

    registry.emit_tool_call(
        name="fs.write",
        session_id="s-1",
        turn_id="t-1",
        task_id="task-1",
        status="ok",
        payload={"path": "notes.md", "api_key": "sk-super-secret", "arguments": {"token": "abc"}},
    )

    assert len(captured) == 1
    event = captured[0]
    assert event.family == "tool_call"
    assert event.name == "fs.write"
    assert event.session_id == "s-1"
    assert event.turn_id == "t-1"
    assert event.schema_version == OBSERVER_SCHEMA_VERSION
    assert event.payload["path"] == "notes.md"
    assert event.payload["api_key"] == "[redacted]"
    assert event.payload["arguments"]["token"] == "[redacted]"


def test_observer_failure_is_fail_open():
    registry = ObserverRegistry()
    calls: list[str] = []

    def bad(event: ObserverEvent) -> None:
        raise RuntimeError("boom")

    def good(event: ObserverEvent) -> None:
        calls.append(event.name)

    registry.register(bad)
    registry.register(good)

    registry.emit_session_started(session_id="s-1", task_id="task-1", payload={})

    assert calls == ["session.started"]
    errors = registry.failures()
    assert len(errors) == 1
    assert "boom" in errors[0]["error"]


def test_correlation_ids_span_session_turn_and_tool():
    registry = ObserverRegistry()
    captured: list[ObserverEvent] = []
    registry.register(captured.append)

    correlation = "corr-42"
    registry.emit_session_started(session_id="s-9", task_id="task-9", correlation_id=correlation, payload={})
    registry.emit_turn_started(
        session_id="s-9", turn_id="t-9", task_id="task-9", correlation_id=correlation, payload={}
    )
    registry.emit_tool_call(
        name="fs.read",
        session_id="s-9",
        turn_id="t-9",
        task_id="task-9",
        correlation_id=correlation,
        status="ok",
        payload={"path": "a.txt"},
    )

    assert [event.family for event in captured] == ["session", "turn", "tool_call"]
    assert {event.correlation_id for event in captured} == {correlation}
    assert {event.session_id for event in captured} == {"s-9"}


def test_approval_and_subagent_events_are_recorded_and_exportable(tmp_path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    registry = ObserverRegistry()
    registry.register(store.record)

    registry.emit_approval(
        session_id="s-1",
        turn_id="t-1",
        task_id="task-1",
        status="granted",
        payload={"decision": "allow", "authorization": "Bearer sekret"},
    )
    registry.emit_subagent(
        name="explore",
        session_id="s-1",
        turn_id="t-1",
        task_id="task-1",
        status="completed",
        payload={"summary": "ok"},
    )
    registry.emit_job(
        name="memory-index",
        session_id="s-1",
        turn_id="t-1",
        task_id="task-1",
        status="ok",
        payload={"indexed": 3},
    )

    out_path = tmp_path / "export.jsonl"
    lines = store.export(out_path)

    payloads = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    families = [event["family"] for event in payloads]
    assert families == ["approval", "subagent", "job"]
    assert payloads[0]["payload"]["authorization"] == "[redacted]"
    assert lines == 3


def test_telemetry_export_jsonl_is_deterministic_and_filterable(tmp_path):
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    registry = ObserverRegistry()
    registry.register(store.record)

    registry.emit_tool_call(
        name="fs.read", session_id="s", turn_id="t", task_id="task", status="ok", payload={}, timestamp="2026-07-01T00:00:00+00:00"
    )
    registry.emit_provider_request(
        name="openai.chat",
        session_id="s",
        turn_id="t",
        task_id="task",
        status="ok",
        payload={"model": "fake"},
        timestamp="2026-07-01T00:00:01+00:00",
    )
    registry.emit_tool_call(
        name="fs.write",
        session_id="s",
        turn_id="t",
        task_id="task",
        status="ok",
        payload={},
        timestamp="2026-07-01T00:00:02+00:00",
    )

    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    store.export(first)
    store.export(second)
    assert first.read_bytes() == second.read_bytes()

    filtered_path = tmp_path / "filtered.jsonl"
    filtered_lines = store.export(filtered_path, families=["tool_call"])
    filtered = [json.loads(line) for line in filtered_path.read_text(encoding="utf-8").splitlines()]
    assert filtered_lines == 2
    assert {event["family"] for event in filtered} == {"tool_call"}


def test_cli_telemetry_export_writes_jsonl(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = TelemetryStore(tmp_path / "telemetry.jsonl")
    registry = ObserverRegistry()
    registry.register(store.record)
    registry.emit_tool_call(
        name="fs.read",
        session_id="s",
        turn_id="t",
        task_id="task",
        status="ok",
        payload={"api_key": "sk-x"},
    )

    out = tmp_path / "out.jsonl"
    exit_code = main(
        [
            "telemetry",
            "export",
            "--input",
            str(tmp_path / "telemetry.jsonl"),
            "--output",
            str(out),
            "--format",
            "jsonl",
            "--redact",
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Telemetry Export" in captured
    payloads = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert payloads[0]["payload"]["api_key"] == "[redacted]"


def test_cli_telemetry_export_returns_zero_when_no_events(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "empty.jsonl"
    exit_code = main(
        [
            "telemetry",
            "export",
            "--input",
            str(tmp_path / "missing.jsonl"),
            "--output",
            str(out),
            "--format",
            "jsonl",
            "--redact",
        ]
    )
    assert exit_code == 0
    assert "no telemetry events" in capsys.readouterr().out
