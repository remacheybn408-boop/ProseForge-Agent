"""Internal agent tool registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True)
class AgentTool:
    """One named internal action exposed to the Agent Kernel."""

    name: str
    permission: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    callable: Callable[[dict[str, Any]], dict[str, Any]]
    description: str = ""
    enabled: bool = True


class ToolRegistry:
    """Register, list, and invoke internal tools."""

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        if "/" in tool.name or "\\" in tool.name:
            raise ConfigurationError("tool names must use dot notation, not paths")
        if tool.name in self._tools:
            raise ConfigurationError(f"tool {tool.name!r} is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> AgentTool | None:
        return self._tools.get(name)

    def list(self) -> list[AgentTool]:
        return [self._tools[name] for name in sorted(self._tools)]

    def required_permission(self, name: str) -> str:
        tool = self.get(name)
        if tool is None:
            raise ConfigurationError(f"unknown tool {name!r}")
        return tool.permission

    def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.invoke(name, payload)

    def invoke(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        audit_events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        tool = self.get(name)
        if tool is None:
            raise ConfigurationError(f"unknown tool {name!r}")
        self._validate_payload(tool, payload)
        try:
            result = tool.callable(payload)
        except Exception as exc:  # noqa: BLE001 - audit before surfacing
            if audit_events is not None:
                audit_events.append(
                    {"tool": name, "permission": tool.permission, "status": "error", "error": str(exc)}
                )
            raise
        if audit_events is not None:
            audit_events.append({"tool": name, "permission": tool.permission, "status": "ok"})
        return result

    @staticmethod
    def _validate_payload(tool: AgentTool, payload: dict[str, Any]) -> None:
        required = tool.input_schema.get("required", [])
        missing = [name for name in required if name not in payload]
        if missing:
            raise ConfigurationError(
                f"tool {tool.name!r} payload missing required field(s): {', '.join(missing)}"
            )


def _ok(name: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def call(payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "tool": name, "payload": payload}

    return call


def default_tool_registry() -> ToolRegistry:
    """Build the current set of built-in tool declarations."""
    registry = ToolRegistry()
    for name, permission, description in (
        ("memory.search", "read_only", "Search memory records"),
        ("memory.add_candidate", "draft_write", "Add a memory candidate"),
        ("workflow.start", "draft_write", "Start a workflow handoff"),
        ("workflow.continue", "project_write", "Continue workflow state"),
        ("chapter.prepare", "draft_write", "Prepare chapter context"),
        ("chapter.run", "draft_write", "Draft chapter artifacts"),
        ("chapter.accept", "project_write", "Accept chapter output"),
        ("provider.certify", "draft_write", "Write provider certification records"),
        ("install.doctor", "read_only", "Run installation diagnostics"),
        ("install.shell_completion", "system_write", "Install shell completions"),
        ("report.render", "read_only", "Render reports"),
    ):
        registry.register(
            AgentTool(
                name=name,
                permission=permission,
                input_schema={},
                output_schema={},
                callable=_ok(name),
                description=description,
            )
        )
    return registry


__all__ = ["AgentTool", "ToolRegistry", "default_tool_registry"]
