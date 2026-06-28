from pathlib import Path

import pytest
import yaml

from proseforge_agent.agent.permissions import PermissionPolicy
from proseforge_agent.agent.tools import AgentTool, ToolRegistry, default_tool_registry
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError


FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "tool_registry.yaml"


def test_read_only_session_cannot_run_project_write_tool():
    registry = ToolRegistry()
    registry.register(
        AgentTool(
            name="chapter.accept",
            permission="project_write",
            input_schema={},
            output_schema={},
            callable=lambda payload: {"ok": True},
        )
    )
    decision = PermissionPolicy().authorize("chapter.accept", permission_level="read_only", registry=registry)
    assert decision.status == "denied"
    assert "project_write" in decision.reason


def test_duplicate_tool_name_is_rejected():
    registry = ToolRegistry()
    tool = AgentTool(
        name="report.render",
        permission="read_only",
        input_schema={},
        output_schema={},
        callable=lambda payload: payload,
    )
    registry.register(tool)
    with pytest.raises(ConfigurationError):
        registry.register(tool)


def test_draft_write_allows_chapter_draft_but_not_accept():
    registry = default_tool_registry()
    policy = PermissionPolicy()
    draft = policy.authorize("chapter.run", permission_level="draft_write", registry=registry)
    accept = policy.authorize("chapter.accept", permission_level="draft_write", registry=registry)
    assert draft.status == "allowed"
    assert accept.status == "denied"


def test_system_write_requires_explicit_confirm():
    registry = default_tool_registry()
    decision = PermissionPolicy().authorize(
        "install.shell_completion",
        permission_level="system_write",
        registry=registry,
    )
    assert decision.status == "confirm_required"
    assert decision.confirmation_prompt


def test_tool_invocation_records_audit_event():
    registry = ToolRegistry()
    registry.register(
        AgentTool(
            name="echo",
            permission="read_only",
            input_schema={"required": ["text"]},
            output_schema={},
            callable=lambda payload: {"echo": payload["text"]},
        )
    )
    audit = []
    result = registry.invoke("echo", {"text": "hi"}, audit_events=audit)
    assert result == {"echo": "hi"}
    assert audit[0]["tool"] == "echo"
    assert audit[0]["status"] == "ok"


def test_registry_exposes_kernel_tool_interface():
    registry = default_tool_registry()
    assert registry.required_permission("chapter.run") == "draft_write"
    result = registry.execute("chapter.run", {"chapter": 1})
    assert result["ok"] is True


def test_unknown_tool_returns_controlled_denial():
    decision = PermissionPolicy().authorize(
        "missing.tool",
        permission_level="system_write",
        registry=default_tool_registry(),
    )
    assert decision.status == "denied"
    assert "unknown" in decision.reason


def test_schema_mismatch_is_reported_before_execution():
    registry = ToolRegistry()
    called = []
    registry.register(
        AgentTool(
            name="echo",
            permission="read_only",
            input_schema={"required": ["text"]},
            output_schema={},
            callable=lambda payload: called.append(payload),
        )
    )
    with pytest.raises(ConfigurationError):
        registry.invoke("echo", {}, audit_events=[])
    assert called == []


def test_tool_registry_fixture_is_portable():
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert data["tools"][0]["name"] == "memory.search"
    assert "/" not in data["tools"][0]["name"]


def test_tools_list_cli_includes_permissions(capsys):
    code = main(["tools", "list", "--include-permissions"])
    out = capsys.readouterr().out
    assert code == 0
    assert "memory.search" in out
    assert "read_only" in out
