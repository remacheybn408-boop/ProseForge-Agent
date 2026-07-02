"""Internal agent tool registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True)
class ToolResult:
    """Structured result returned by agent tools."""

    ok: bool
    output: Any = ""
    error: str = ""
    provenance: str = "internal"
    summary: str = ""
    artifact_refs: list[Any] = field(default_factory=list)
    truncated: bool = False
    redaction_applied: bool = False


@dataclass(frozen=True)
class ToolContext:
    """Execution context shared by general tools."""

    workspace_root: Path
    permission_level: str = "read_only"
    network_enabled: bool = False
    http_client: Any | None = None


@dataclass(frozen=True)
class AgentTool:
    """One named internal action exposed to the Agent Kernel."""

    name: str
    permission: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    callable: Callable[..., Any]
    description: str = ""
    domain: str = "agent"
    aliases: tuple[str, ...] = ()
    enabled: bool = True

    def invoke(self, payload: dict[str, Any], context: ToolContext | None = None) -> Any:
        if context is None:
            return self.callable(payload)
        return self.callable(payload, context)


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

    def list(self, *, domain: str | None = None) -> list[AgentTool]:
        tools = [self._tools[name] for name in sorted(self._tools)]
        if domain is None:
            return tools
        return [tool for tool in tools if tool.domain == domain]

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
        context: ToolContext | None = None,
        audit_events: list[dict[str, Any]] | None = None,
    ) -> Any:
        tool = self.get(name)
        if tool is None:
            raise ConfigurationError(f"unknown tool {name!r}")
        if not tool.enabled:
            # A disabled tool must never execute — otherwise a stub could return
            # a fake success. See finding 1.9.
            raise ConfigurationError(f"tool {name!r} is disabled")
        self._validate_payload(tool, payload)
        try:
            result = tool.invoke(payload, context)
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


def _writing_result(tool_name: str, operation: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def call(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "tool": tool_name,
            "result": {
                "operation": operation,
                "structured": True,
                "status": "planned",
                "input": dict(payload),
                "sections": [],
                "warnings": [],
            },
        }

    return call


def _require_context(context: ToolContext | None) -> ToolContext:
    if context is None:
        raise ConfigurationError("tool context is required")
    return context


def _resolve_workspace_path(context: ToolContext, raw_path: str) -> Path:
    root = context.workspace_root.resolve()
    candidate = (root / raw_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ConfigurationError(f"path escapes workspace: {raw_path}")
    return candidate


def _fs_read(payload: dict[str, Any], context: ToolContext | None = None) -> ToolResult:
    ctx = _require_context(context)
    path = _resolve_workspace_path(ctx, str(payload["path"]))
    return ToolResult(ok=True, output=path.read_text(encoding="utf-8"), provenance="workspace")


def _fs_write(payload: dict[str, Any], context: ToolContext | None = None) -> ToolResult:
    ctx = _require_context(context)
    path = _resolve_workspace_path(ctx, str(payload["path"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(payload["text"]), encoding="utf-8")
    return ToolResult(ok=True, output=str(path.relative_to(ctx.workspace_root.resolve())), provenance="workspace")


def _fs_edit(payload: dict[str, Any], context: ToolContext | None = None) -> ToolResult:
    ctx = _require_context(context)
    old = str(payload["old"])
    if not old:
        # An empty `old` would make str.replace prepend `new` to the file
        # ("" in text is always True). Refuse it so a rewritten/crafted request
        # cannot inject content at the file head. See finding 1.7.
        return ToolResult(ok=False, error="old must be non-empty", provenance="workspace")
    path = _resolve_workspace_path(ctx, str(payload["path"]))
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return ToolResult(ok=False, error="old text not found", provenance="workspace")
    path.write_text(text.replace(old, str(payload["new"]), 1), encoding="utf-8")
    return ToolResult(ok=True, output=str(path.relative_to(ctx.workspace_root.resolve())), provenance="workspace")


def _web_fetch(payload: dict[str, Any], context: ToolContext | None = None) -> ToolResult:
    ctx = _require_context(context)
    if not ctx.network_enabled:
        return ToolResult(ok=False, error="network permission required", provenance="untrusted")
    if ctx.http_client is None:
        return ToolResult(ok=False, error="http client is required", provenance="untrusted")
    return ToolResult(ok=True, output=ctx.http_client.get_text(str(payload["url"])), provenance="untrusted")


def _web_search(payload: dict[str, Any], context: ToolContext | None = None) -> ToolResult:
    ctx = _require_context(context)
    if not ctx.network_enabled:
        return ToolResult(ok=False, error="network permission required", provenance="untrusted")
    if ctx.http_client is None:
        return ToolResult(ok=False, error="http client is required", provenance="untrusted")
    return ToolResult(ok=True, output=ctx.http_client.search(str(payload["query"])), provenance="untrusted")


def register_general_tools(registry: ToolRegistry) -> ToolRegistry:
    """Register general filesystem and web tools."""
    for tool in (
        AgentTool(
            name="fs.read",
            permission="read_only",
            input_schema={"required": ["path"]},
            output_schema={},
            callable=_fs_read,
            description="Read a UTF-8 file inside the workspace",
        ),
        AgentTool(
            name="fs.write",
            permission="draft_write",
            input_schema={"required": ["path", "text"]},
            output_schema={},
            callable=_fs_write,
            description="Write a UTF-8 file inside the workspace",
        ),
        AgentTool(
            name="fs.edit",
            permission="draft_write",
            input_schema={"required": ["path", "old", "new"]},
            output_schema={},
            callable=_fs_edit,
            description="Replace text in a UTF-8 file inside the workspace",
        ),
        AgentTool(
            name="web.fetch",
            permission="read_only",
            input_schema={"required": ["url"]},
            output_schema={},
            callable=_web_fetch,
            description="Fetch web text through the injected HTTP client",
        ),
        AgentTool(
            name="web.search",
            permission="read_only",
            input_schema={"required": ["query"]},
            output_schema={},
            callable=_web_search,
            description="Search the web through the injected HTTP client",
        ),
    ):
        registry.register(tool)
    return registry


def general_tool_registry() -> ToolRegistry:
    """Build a registry containing only general-purpose tools."""
    return register_general_tools(ToolRegistry())


def register_writing_domain_tools(registry: ToolRegistry) -> ToolRegistry:
    """Register built-in writing domain tools as agent-callable declarations."""
    output_schema = {"required": ["ok", "tool", "result"]}
    specs = (
        (
            "writing.expand_scene",
            "/expand-scene",
            "expand_scene",
            "draft_write",
            "Expand a scene while preserving canon intent",
            ["text"],
        ),
        (
            "writing.condense_chapter",
            "/condense-chapter",
            "condense_chapter",
            "draft_write",
            "Condense a chapter into a tighter draft",
            ["text"],
        ),
        (
            "writing.polish_dialogue",
            "/polish-dialogue",
            "polish_dialogue",
            "draft_write",
            "Polish dialogue beats without changing plot facts",
            ["text"],
        ),
        (
            "writing.enhance_description",
            "/enhance-description",
            "enhance_description",
            "draft_write",
            "Enhance sensory and setting description",
            ["text"],
        ),
        (
            "writing.check_chronology",
            "/check-chronology",
            "check_chronology",
            "read_only",
            "Check chronology against timeline evidence",
            ["text"],
        ),
        (
            "writing.suggest_title",
            "/suggest-title",
            "suggest_title",
            "draft_write",
            "Suggest structured title candidates",
            ["text"],
        ),
        (
            "writing.outline_chapter",
            "/outline-chapter",
            "outline_chapter",
            "draft_write",
            "Outline a chapter from goal and evidence",
            ["goal"],
        ),
    )
    for name, alias, operation, permission, description, required in specs:
        registry.register(
            AgentTool(
                name=name,
                permission=permission,
                input_schema={"required": required},
                output_schema=output_schema,
                callable=_writing_result(name, operation),
                description=description,
                domain="writing",
                aliases=(alias,),
            )
        )
    return registry


def default_tool_registry() -> ToolRegistry:
    """Build the current set of built-in tool declarations.

    The tools registered in the explicit loop below use planning-stub callables
    (`_ok`): their real execution lives in the CLI ``_handle_*`` handlers. They
    are kept ``enabled=True`` because the kernel tool interface and
    ``function_calling`` depend on them returning a planned result. To make a
    tool refuse execution, register it with ``enabled=False`` — ``invoke`` now
    rejects disabled tools (finding 1.9).
    """
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
    register_writing_domain_tools(registry)
    register_general_tools(registry)
    return registry


__all__ = [
    "AgentTool",
    "ToolContext",
    "ToolRegistry",
    "ToolResult",
    "default_tool_registry",
    "general_tool_registry",
    "register_general_tools",
    "register_writing_domain_tools",
]
