"""Middleware hooks and trajectory datasets tests (Task 182)."""

from __future__ import annotations

import json

from proseforge_agent.agent.middleware import (
    MIDDLEWARE_KIND_LLM_EXECUTION,
    MIDDLEWARE_KIND_LLM_REQUEST,
    MIDDLEWARE_KIND_TOOL_EXECUTION,
    MIDDLEWARE_KIND_TOOL_REQUEST,
    MiddlewareRegistry,
    MiddlewareTrace,
    ToolRequest,
    ToolExecutionContext,
)
from proseforge_agent.agent.permissions import PermissionPolicy
from proseforge_agent.agent.tools import AgentTool, ToolContext, ToolRegistry, ToolResult
from proseforge_agent.cli import main
from proseforge_agent.eval.trajectories import (
    TRAJECTORY_SCHEMA_VERSION,
    TrajectoryDatasetExporter,
    TrajectoryStep,
    TrajectoryStore,
)


def _echo_tool(name: str = "echo") -> AgentTool:
    def invoke(payload: dict, ctx: ToolContext | None = None) -> ToolResult:
        return ToolResult(ok=True, output=payload, provenance=f"tool:{name}")

    return AgentTool(
        name=name,
        permission="read_only",
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        callable=invoke,
    )


def test_tool_request_middleware_rewrites_args_before_policy(tmp_path):
    registry = MiddlewareRegistry()

    def strip_secret(request: ToolRequest) -> ToolRequest:
        args = dict(request.arguments)
        args["prompt"] = args.get("prompt", "").replace("SECRET", "[redacted]")
        return request.with_arguments(args)

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "strip_secret", strip_secret, enabled=True)

    tool_registry = ToolRegistry()
    tool_registry.register(_echo_tool("fs.read"))
    policy = PermissionPolicy()

    original = ToolRequest(tool_name="fs.read", arguments={"prompt": "hello SECRET world"})
    rewritten = registry.apply_tool_request(original)

    assert rewritten.arguments["prompt"] == "hello [redacted] world"

    decision = policy.authorize(
        rewritten.tool_name, permission_level="read_only", registry=tool_registry
    )
    assert decision.status == "allowed"

    traces = registry.traces()
    assert traces[0].kind == MIDDLEWARE_KIND_TOOL_REQUEST
    assert traces[0].name == "strip_secret"
    assert traces[0].rewritten is True


def test_disabled_middleware_is_skipped():
    registry = MiddlewareRegistry()
    calls: list[str] = []

    def rewriter(request: ToolRequest) -> ToolRequest:
        calls.append(request.tool_name)
        return request.with_arguments({"changed": True})

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "off", rewriter, enabled=False)
    original = ToolRequest(tool_name="fs.read", arguments={"a": 1})
    result = registry.apply_tool_request(original)

    assert calls == []
    assert result.arguments == {"a": 1}
    assert registry.traces() == []


def test_middleware_failure_is_fail_open():
    registry = MiddlewareRegistry()

    def bad(request: ToolRequest) -> ToolRequest:
        raise RuntimeError("boom")

    def good(request: ToolRequest) -> ToolRequest:
        return request.with_arguments({**request.arguments, "seen": True})

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "bad", bad, enabled=True)
    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "good", good, enabled=True)

    result = registry.apply_tool_request(ToolRequest(tool_name="fs.read", arguments={}))
    assert result.arguments == {"seen": True}

    failures = registry.failures()
    assert len(failures) == 1
    assert failures[0]["name"] == "bad"


def test_ordered_middleware_execution_is_deterministic():
    registry = MiddlewareRegistry()

    def a(request: ToolRequest) -> ToolRequest:
        return request.with_arguments({**request.arguments, "chain": request.arguments.get("chain", "") + "A"})

    def b(request: ToolRequest) -> ToolRequest:
        return request.with_arguments({**request.arguments, "chain": request.arguments.get("chain", "") + "B"})

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "a", a, enabled=True)
    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "b", b, enabled=True)

    result = registry.apply_tool_request(ToolRequest(tool_name="fs.read", arguments={}))
    assert result.arguments["chain"] == "AB"


def test_tool_execution_middleware_wraps_next_call():
    registry = MiddlewareRegistry()

    def wrapper(ctx: ToolExecutionContext, next_call):
        result = next_call(ctx)
        return ToolResult(
            ok=result.ok,
            output={"wrapped": True, "inner": result.output},
            error=result.error,
            provenance=result.provenance,
        )

    registry.register(MIDDLEWARE_KIND_TOOL_EXECUTION, "wrap", wrapper, enabled=True)

    def base(ctx: ToolExecutionContext) -> ToolResult:
        return ToolResult(ok=True, output={"raw": True}, provenance="tool:fs.read")

    result = registry.apply_tool_execution(
        ToolExecutionContext(tool_name="fs.read", arguments={"path": "notes.md"}),
        base,
    )
    assert result.ok is True
    assert result.output == {"wrapped": True, "inner": {"raw": True}}


def test_llm_middleware_kinds_are_recognized():
    registry = MiddlewareRegistry()
    registry.register(MIDDLEWARE_KIND_LLM_REQUEST, "log", lambda req: req, enabled=True)
    registry.register(MIDDLEWARE_KIND_LLM_EXECUTION, "wrap", lambda ctx, nxt: nxt(ctx), enabled=True)
    assert set(registry.middleware_names(MIDDLEWARE_KIND_LLM_REQUEST)) == {"log"}
    assert set(registry.middleware_names(MIDDLEWARE_KIND_LLM_EXECUTION)) == {"wrap"}


def test_trajectory_export_is_redacted_and_schema_versioned(tmp_path):
    store = TrajectoryStore(tmp_path / "trajectories.jsonl")
    store.append(
        TrajectoryStep(
            session_id="s-1",
            turn_id="t-1",
            step_index=0,
            kind="tool_call",
            name="fs.write",
            inputs={"api_key": "sk-super-secret", "path": "notes.md"},
            outputs={"ok": True, "text": "MY PRIVATE DRAFT"},
        )
    )
    store.append(
        TrajectoryStep(
            session_id="s-1",
            turn_id="t-1",
            step_index=1,
            kind="llm_response",
            name="openai.chat",
            inputs={},
            outputs={"content": "generated text"},
        )
    )

    out = tmp_path / "out.jsonl"
    exporter = TrajectoryDatasetExporter(store)
    written = exporter.export(out, redact=True, redact_text_fields=("text",))

    assert written == 2
    lines = out.read_text(encoding="utf-8").splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["schema_version"] == TRAJECTORY_SCHEMA_VERSION
    assert payloads[0]["inputs"]["api_key"] == "[redacted]"
    assert payloads[0]["outputs"]["text"] == "[redacted]"
    assert payloads[1]["outputs"]["content"] == "generated text"


def test_trajectory_export_is_deterministic_and_compressible(tmp_path):
    store = TrajectoryStore(tmp_path / "t.jsonl")
    store.append(
        TrajectoryStep(session_id="s", turn_id="t", step_index=0, kind="tool_call", name="fs.read", inputs={}, outputs={})
    )
    store.append(
        TrajectoryStep(session_id="s", turn_id="t", step_index=1, kind="llm_response", name="openai.chat", inputs={}, outputs={})
    )

    exporter = TrajectoryDatasetExporter(store)
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    exporter.export(first)
    exporter.export(second)
    assert first.read_bytes() == second.read_bytes()

    compressed = tmp_path / "compact.jsonl"
    exporter.export(compressed, compact_fields=("outputs",))
    payloads = [json.loads(line) for line in compressed.read_text(encoding="utf-8").splitlines()]
    for payload in payloads:
        assert payload["outputs"] == {}


def test_cli_trajectories_export_writes_jsonl(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = TrajectoryStore(tmp_path / "trajectories.jsonl")
    store.append(
        TrajectoryStep(
            session_id="s",
            turn_id="t",
            step_index=0,
            kind="tool_call",
            name="fs.read",
            inputs={"api_key": "sk-x"},
            outputs={"ok": True},
        )
    )

    out = tmp_path / "export.jsonl"
    exit_code = main(
        [
            "trajectories",
            "export",
            "--input",
            str(tmp_path / "trajectories.jsonl"),
            "--output",
            str(out),
            "--format",
            "jsonl",
            "--redact",
        ]
    )
    assert exit_code == 0
    text = capsys.readouterr().out
    assert "Trajectory Export" in text
    payloads = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert payloads[0]["inputs"]["api_key"] == "[redacted]"


def test_cli_trajectories_export_returns_zero_when_no_events(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "empty.jsonl"
    exit_code = main(
        [
            "trajectories",
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
    assert "no trajectory steps" in capsys.readouterr().out
