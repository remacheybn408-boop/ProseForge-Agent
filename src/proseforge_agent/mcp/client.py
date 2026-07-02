"""MCP client foundation abstractions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from ..agent.tools import ToolResult
from ..errors import ConfigurationError
from .policy import MCPPolicy, MCPPolicyDecision

if TYPE_CHECKING:  # avoid client<-approval<-credentials<-registry<-client cycle
    from .approval import MCPApprovalGate


@dataclass(frozen=True)
class MCPServerSpec:
    """Connection information for an MCP server."""

    id: str
    transport: str
    command: list[str] = field(default_factory=list)
    url: str = ""
    cwd: str = ""
    env: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPCapabilityReport:
    """Discovered capabilities for one MCP server."""

    server_id: str
    transport: str
    capabilities: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPResource:
    uri: str
    name: str = ""
    mime_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPPrompt:
    name: str
    arguments: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MCPTransport(Protocol):
    def start(self) -> None: ...

    def close(self) -> None: ...

    def capabilities(self) -> dict[str, Any]: ...

    def list_tools(self) -> list[dict[str, Any]]: ...

    def list_resources(self) -> list[dict[str, Any]]: ...

    def list_prompts(self) -> list[dict[str, Any]]: ...

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class StaticMCPTransport:
    """Deterministic in-process transport used by tests and default CLI demo."""

    def __init__(
        self,
        *,
        capabilities: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        prompts: list[dict[str, Any]] | None = None,
        tool_results: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._capabilities = capabilities or {"tools": True, "resources": True, "prompts": True}
        self._tools = tools or []
        self._resources = resources or []
        self._prompts = prompts or []
        self._tool_results = tool_results or {}
        self.started = False
        self.closed = False

    def start(self) -> None:
        self.started = True
        self.closed = False

    def close(self) -> None:
        self.closed = True

    def capabilities(self) -> dict[str, Any]:
        return dict(self._capabilities)

    def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools)

    def list_resources(self) -> list[dict[str, Any]]:
        return list(self._resources)

    def list_prompts(self) -> list[dict[str, Any]]:
        return list(self._prompts)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tool_results:
            return {"ok": False, "error": f"unknown MCP tool {name}", "arguments": arguments}
        return dict(self._tool_results[name])


class StdioMCPTransport:
    """Placeholder for a real stdio MCP process lifecycle."""

    def __init__(self, spec: MCPServerSpec) -> None:
        self.spec = spec
        self.started = False

    def start(self) -> None:
        if not self.spec.command:
            raise ConfigurationError("stdio MCP server requires a command")
        self.started = True

    def close(self) -> None:
        self.started = False

    def capabilities(self) -> dict[str, Any]:
        return {"tools": False, "resources": False, "prompts": False, "placeholder": "stdio"}

    def list_tools(self) -> list[dict[str, Any]]:
        return []

    def list_resources(self) -> list[dict[str, Any]]:
        return []

    def list_prompts(self) -> list[dict[str, Any]]:
        return []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "error": "stdio execution adapter not configured", "tool": name, "arguments": arguments}


class PlaceholderMCPTransport(StdioMCPTransport):
    """HTTP/SSE transport placeholder."""

    def start(self) -> None:
        self.started = True

    def capabilities(self) -> dict[str, Any]:
        return {"tools": False, "resources": False, "prompts": False, "placeholder": self.spec.transport}


class MCPClient:
    """Small provider-neutral MCP client wrapper.

    A client constructed without a ``policy`` performs no policy enforcement and
    is **unsafe for production transports** — it will run any tool the transport
    accepts. Production wiring must pass an :class:`MCPPolicy` (and, for
    write-class tools, an :class:`MCPApprovalGate`). See finding 1.6 of
    ``docs/review/core-review-2026-07-01.md``.
    """

    def __init__(
        self,
        spec: MCPServerSpec,
        *,
        transport: MCPTransport | None = None,
        policy: MCPPolicy | None = None,
        approval_gate: "MCPApprovalGate | None" = None,
    ) -> None:
        self.spec = spec
        self.transport = transport or _transport_for(spec)
        self._policy = policy
        self._approval_gate = approval_gate

    def start(self) -> None:
        self.transport.start()

    def close(self) -> None:
        self.transport.close()

    def inspect(self) -> MCPCapabilityReport:
        return MCPCapabilityReport(
            server_id=self.spec.id,
            transport=self.spec.transport,
            capabilities=self.transport.capabilities(),
        )

    def list_tools(self) -> list[MCPTool]:
        return [
            MCPTool(
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                input_schema=dict(item.get("input_schema") or item.get("inputSchema") or {}),
            )
            for item in self.transport.list_tools()
        ]

    def list_resources(self) -> list[MCPResource]:
        return [
            MCPResource(
                uri=str(item.get("uri", "")),
                name=str(item.get("name", "")),
                mime_type=str(item.get("mime_type", item.get("mimeType", ""))),
            )
            for item in self.transport.list_resources()
        ]

    def list_prompts(self) -> list[MCPPrompt]:
        return [
            MCPPrompt(
                name=str(item.get("name", "")),
                arguments=list(item.get("arguments") or []),
                description=str(item.get("description", "")),
            )
            for item in self.transport.list_prompts()
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        if self._policy is not None:
            blocked = self._enforce_policy(name, arguments)
            if blocked is not None:
                return blocked
        payload = self.transport.call_tool(name, arguments)
        ok = payload.get("ok", True) is not False
        return ToolResult(
            ok=ok,
            output=payload if ok else "",
            error="" if ok else str(payload.get("error", "MCP tool failed")),
            provenance=f"mcp:{self.spec.id}",
        )

    def _enforce_policy(self, name: str, arguments: dict[str, Any]) -> ToolResult | None:
        """Consult policy (and the approval gate) before the transport runs.

        Returns a denial ``ToolResult`` to block the call, or ``None`` to allow
        it. The tool-name -> (operation, target) derivation mirrors
        :meth:`MCPApprovalGate._requires_approval` so both paths agree.
        """
        assert self._policy is not None
        decision = self._decide(name, arguments)
        if not decision.allowed and not decision.requires_approval:
            return ToolResult(
                ok=False,
                error=f"blocked by MCP policy: {decision.reason}",
                provenance=f"mcp:{self.spec.id}",
            )
        if self._approval_gate is not None:
            request = self._approval_gate.enqueue_if_required(
                server_id=self.spec.id,
                tool_name=name,
                arguments=arguments,
                policy=self._policy,
            )
            if request is not None and request.status != "approved":
                return ToolResult(
                    ok=False,
                    error=f"MCP tool requires approval: {request.id}",
                    provenance=f"mcp:{self.spec.id}",
                )
        elif decision.requires_approval:
            return ToolResult(
                ok=False,
                error="MCP tool requires approval but no approval gate is configured",
                provenance=f"mcp:{self.spec.id}",
            )
        return None

    def _decide(self, name: str, arguments: dict[str, Any]) -> MCPPolicyDecision:
        assert self._policy is not None
        target = str(arguments.get("path") or arguments.get("target") or "")
        if not target:
            return MCPPolicyDecision(True, reason="no policy-relevant target")
        lowered = name.lower()
        operation = (
            "fs.write"
            if any(token in lowered for token in ("write", "delete", "remove", "overwrite"))
            else "fs.read"
        )
        return self._policy.decide(operation, target)


def default_demo_client(server_id: str = "filesystem") -> MCPClient:
    spec = MCPServerSpec(id="filesystem", transport="stdio", command=["proseforge-fake-mcp"])
    transport = StaticMCPTransport(
        tools=[{"name": "read_file", "description": "Read a workspace file", "input_schema": {"type": "object"}}],
        resources=[{"uri": "file:///workspace", "name": "workspace"}],
        prompts=[{"name": "summarize", "arguments": ["text"]}],
        tool_results={"read_file": {"content": ""}},
    )
    if server_id != spec.id:
        raise ConfigurationError(f"unknown MCP server {server_id!r}")
    return MCPClient(spec, transport=transport)


def _transport_for(spec: MCPServerSpec) -> MCPTransport:
    if spec.transport == "stdio":
        return StdioMCPTransport(spec)
    if spec.transport in {"http", "sse"}:
        return PlaceholderMCPTransport(spec)
    raise ConfigurationError(f"unsupported MCP transport {spec.transport!r}")


__all__ = [
    "MCPCapabilityReport",
    "MCPClient",
    "MCPPrompt",
    "MCPResource",
    "MCPServerSpec",
    "MCPTool",
    "MCPTransport",
    "PlaceholderMCPTransport",
    "StaticMCPTransport",
    "StdioMCPTransport",
    "default_demo_client",
]
