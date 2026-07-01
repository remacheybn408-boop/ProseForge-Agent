"""Foundation for managed external tool gateways."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any

from ...agent.permissions import PERMISSION_LEVELS


_PERMISSION_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class ManagedToolDeclaration:
    """Declaration for one managed tool exposed through a gateway."""

    name: str
    permission: str = "read_only"
    credential_scope: str = ""
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    output_limit: int = 4096
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "permission": self.permission,
            "credential_scope": self.credential_scope,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "output_limit": self.output_limit,
            "enabled": self.enabled,
        }


@dataclass(frozen=True)
class ManagedToolInvocationContext:
    """Per-call policy context for a managed tool invocation."""

    permission_ceiling: str = "read_only"
    credential_scopes: set[str] = field(default_factory=set)
    provider: str = "fake"


@dataclass(frozen=True)
class ManagedToolResult:
    """Structured result from the managed gateway."""

    status: str
    tool: str
    reason: str = ""
    required_permission: str = "read_only"
    output: dict[str, Any] = field(default_factory=dict)
    credentials: dict[str, str] = field(default_factory=dict)
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tool": self.tool,
            "reason": self.reason,
            "required_permission": self.required_permission,
            "output": self.output,
            "credentials": self.credentials,
            "truncated": self.truncated,
        }


class ManagedToolGateway:
    """Permission-aware gateway for managed external tools."""

    def __init__(
        self,
        declarations: list[ManagedToolDeclaration] | None = None,
        *,
        credentials: dict[str, str] | None = None,
    ) -> None:
        self._declarations = {tool.name: tool for tool in declarations or default_declarations()}
        self._credentials = dict(credentials or {})

    @classmethod
    def fake(
        cls,
        declarations: list[ManagedToolDeclaration] | None = None,
        *,
        credentials: dict[str, str] | None = None,
    ) -> "ManagedToolGateway":
        return cls(declarations, credentials=credentials or {"web": "fake-web-secret"})

    def list(self) -> list[ManagedToolDeclaration]:
        return [self._declarations[name] for name in sorted(self._declarations)]

    def get(self, name: str) -> ManagedToolDeclaration | None:
        return self._declarations.get(name)

    def invoke(
        self,
        tool_name: str,
        payload: dict[str, Any],
        context: ManagedToolInvocationContext | None = None,
    ) -> ManagedToolResult:
        context = context or ManagedToolInvocationContext()
        declaration = self.get(tool_name)
        if declaration is None:
            return ManagedToolResult(
                status="unknown_tool",
                tool=tool_name,
                reason=f"{tool_name} is not declared by this managed gateway",
            )
        if not declaration.enabled:
            return ManagedToolResult(
                status="denied",
                tool=tool_name,
                reason=f"{tool_name} is disabled",
                required_permission=declaration.permission,
            )
        if _permission_rank(context.permission_ceiling) < _permission_rank(declaration.permission):
            return ManagedToolResult(
                status="denied",
                tool=tool_name,
                reason=f"{tool_name} requires {declaration.permission}, ceiling is {context.permission_ceiling}",
                required_permission=declaration.permission,
            )
        if declaration.credential_scope:
            if declaration.credential_scope not in context.credential_scopes:
                return ManagedToolResult(
                    status="denied",
                    tool=tool_name,
                    reason=f"{tool_name} requires credential scope {declaration.credential_scope}",
                    required_permission=declaration.permission,
                )
            if declaration.credential_scope not in self._credentials:
                return ManagedToolResult(
                    status="denied",
                    tool=tool_name,
                    reason=f"{tool_name} credential scope {declaration.credential_scope} is not configured",
                    required_permission=declaration.permission,
                )

        output, truncated = _bounded_output(
            {"ok": True, "tool": tool_name, "payload": dict(payload)},
            declaration.output_limit,
        )
        credentials = (
            {declaration.credential_scope: "[redacted]"} if declaration.credential_scope else {}
        )
        return ManagedToolResult(
            status="ok",
            tool=tool_name,
            reason=f"{tool_name} executed through {context.provider} gateway",
            required_permission=declaration.permission,
            output=output,
            credentials=credentials,
            truncated=truncated,
        )


def default_declarations() -> list[ManagedToolDeclaration]:
    return [
        ManagedToolDeclaration(
            name="web.search",
            permission="read_only",
            credential_scope="web",
            description="Search the web through a managed provider",
            input_schema={"required": ["query"]},
            output_schema={"type": "citation_candidates"},
        ),
        ManagedToolDeclaration(
            name="url.inspect",
            permission="read_only",
            credential_scope="web",
            description="Inspect URL safety and metadata",
            input_schema={"required": ["url"]},
            output_schema={"type": "url_safety_decision"},
        ),
    ]


def _permission_rank(permission: str) -> int:
    return _PERMISSION_ORDER.get(permission, -1)


def _bounded_output(output: dict[str, Any], limit: int) -> tuple[dict[str, Any], bool]:
    text = json.dumps(output, ensure_ascii=False, sort_keys=True)
    if len(text) <= limit:
        return output, False
    return {"preview": text[:limit], "truncated": True}, True


__all__ = [
    "ManagedToolDeclaration",
    "ManagedToolGateway",
    "ManagedToolInvocationContext",
    "ManagedToolResult",
    "default_declarations",
]
