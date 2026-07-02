"""Harden fs.edit empty-old + ToolRegistry disabled-tool gate (Task 199)."""

from __future__ import annotations

import pytest

from proseforge_agent.agent.tools import AgentTool, ToolContext, ToolRegistry, _fs_edit
from proseforge_agent.errors import ConfigurationError


def _ctx(tmp_path):
    return ToolContext(workspace_root=tmp_path, permission_level="project_write")


def test_fs_edit_rejects_empty_old_without_modifying_file(tmp_path):
    target = tmp_path / "canon.md"
    target.write_text("ORIGINAL\n", encoding="utf-8")

    result = _fs_edit({"path": "canon.md", "old": "", "new": "<INJECTED>"}, _ctx(tmp_path))

    assert result.ok is False
    assert "non-empty" in result.error
    assert target.read_text(encoding="utf-8") == "ORIGINAL\n"  # unchanged


def test_fs_edit_still_replaces_when_old_is_present(tmp_path):
    target = tmp_path / "canon.md"
    target.write_text("hello world\n", encoding="utf-8")

    result = _fs_edit({"path": "canon.md", "old": "world", "new": "there"}, _ctx(tmp_path))

    assert result.ok is True
    assert target.read_text(encoding="utf-8") == "hello there\n"


def test_fs_edit_reports_missing_old_text(tmp_path):
    target = tmp_path / "canon.md"
    target.write_text("hello\n", encoding="utf-8")
    result = _fs_edit({"path": "canon.md", "old": "absent", "new": "x"}, _ctx(tmp_path))
    assert result.ok is False
    assert "not found" in result.error


def _make_registry(enabled: bool) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        AgentTool(
            name="stub.tool",
            permission="read_only",
            input_schema={},
            output_schema={},
            callable=lambda payload: {"ok": True, "tool": "stub.tool"},
            enabled=enabled,
        )
    )
    return registry


def test_registry_invoke_refuses_disabled_tool():
    registry = _make_registry(enabled=False)
    with pytest.raises(ConfigurationError) as exc:
        registry.invoke("stub.tool", {})
    assert "disabled" in str(exc.value)


def test_registry_invoke_runs_enabled_tool():
    registry = _make_registry(enabled=True)
    result = registry.invoke("stub.tool", {})
    assert result["ok"] is True
