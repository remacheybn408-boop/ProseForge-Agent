"""Offline mode policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class OfflineDecision:
    """Decision for one action under offline mode."""

    allowed: bool
    reason: str = ""
    feature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OfflinePolicy:
    """Allow local capabilities and block remote/dependent operations."""

    allowed_features = (
        "project doctor",
        "manifest validate",
        "txt/markdown export",
        "keyword search",
        "stats",
        "backup",
        "fake provider chat",
        "local memory read",
    )
    blocked_features = (
        "remote provider call",
        "MCP network tools",
        "model catalog update",
        "cloud sync",
    )

    def check(
        self,
        command: str,
        *,
        provider: str | None = None,
        export_format: str | None = None,
        tool_name: str | None = None,
    ) -> OfflineDecision:
        if command == "chat":
            if (provider or "fake") == "fake":
                return OfflineDecision(True, feature="fake provider chat")
            return OfflineDecision(False, "remote provider calls are blocked in offline mode", "remote provider call")
        if command == "mcp":
            if tool_name and tool_name.startswith("network."):
                return OfflineDecision(False, "MCP network tools are blocked in offline mode", "MCP network tools")
            return OfflineDecision(True, feature="MCP local metadata")
        if command == "export":
            if (export_format or "txt") in {"txt", "markdown", "md"}:
                return OfflineDecision(True, feature="txt/markdown export")
            return OfflineDecision(False, "only txt/markdown export is available offline", "export")
        if command in {"doctor", "project", "search", "stats", "backup", "memory", "offline"}:
            return OfflineDecision(True, feature=command)
        if command in {"provider", "upgrade", "service", "support"}:
            return OfflineDecision(False, f"{command} may require remote or system dependencies", command)
        if command == "cloud_sync":
            return OfflineDecision(False, "cloud sync is blocked in offline mode", "cloud sync")
        return OfflineDecision(True, feature=command)

    def status(self) -> dict[str, Any]:
        return {
            "offline": True,
            "allowed": list(self.allowed_features),
            "blocked": list(self.blocked_features),
        }


__all__ = ["OfflineDecision", "OfflinePolicy"]
