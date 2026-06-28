"""Permission policy for chat-driven tool execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tools import ToolRegistry


PERMISSION_LEVELS: tuple[str, ...] = (
    "read_only",
    "draft_write",
    "project_write",
    "engine_write",
    "system_write",
)
_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class PermissionDecision:
    """Authorization result for one tool attempt."""

    status: str
    reason: str
    required_permission: str
    confirmation_prompt: str = ""
    audit_event: dict[str, Any] = field(default_factory=dict)


class PermissionPolicy:
    """Authorize tool use against a session permission ceiling."""

    def authorize(
        self,
        tool_name: str,
        *,
        permission_level: str,
        registry: ToolRegistry,
        session_context: dict[str, Any] | None = None,
    ) -> PermissionDecision:
        tool = registry.get(tool_name)
        if tool is None:
            return self._decision(
                status="denied",
                reason=f"unknown tool {tool_name!r}",
                required_permission="read_only",
                tool_name=tool_name,
            )

        if _ORDER.get(permission_level, -1) < _ORDER.get(tool.permission, 0):
            return self._decision(
                status="denied",
                reason=f"{tool_name} requires {tool.permission}, session has {permission_level}",
                required_permission=tool.permission,
                tool_name=tool_name,
            )

        if tool.permission == "system_write":
            confirmed = set((session_context or {}).get("confirmed_tools", []))
            if tool_name not in confirmed:
                return self._decision(
                    status="confirm_required",
                    reason=f"{tool_name} requires explicit system_write confirmation",
                    required_permission=tool.permission,
                    tool_name=tool_name,
                    confirmation_prompt=f"Confirm system-write tool {tool_name} for this turn.",
                )

        return self._decision(
            status="allowed",
            reason=f"{tool_name} allowed at {permission_level}",
            required_permission=tool.permission,
            tool_name=tool_name,
        )

    @staticmethod
    def _decision(
        *,
        status: str,
        reason: str,
        required_permission: str,
        tool_name: str,
        confirmation_prompt: str = "",
    ) -> PermissionDecision:
        return PermissionDecision(
            status=status,
            reason=reason,
            required_permission=required_permission,
            confirmation_prompt=confirmation_prompt,
            audit_event={
                "tool": tool_name,
                "status": status,
                "required_permission": required_permission,
                "reason": reason,
            },
        )


__all__ = ["PERMISSION_LEVELS", "PermissionDecision", "PermissionPolicy"]
