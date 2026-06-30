"""MCP security policy boundary."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath, Path
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True)
class MCPPolicyDecision:
    """Decision for one MCP action under policy."""

    allowed: bool
    requires_approval: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPPolicy:
    """Per-server security boundary for MCP operations."""

    server_id: str
    filesystem_allow: list[str] = field(default_factory=list)
    filesystem_deny: list[str] = field(default_factory=list)
    network_allow: list[str] = field(default_factory=list)
    command_allow: list[str] = field(default_factory=list)
    secrets_allowed: bool = False
    project_scope: str = ""
    write_mode: str = "approval_required"

    def decide(self, operation: str, target: str) -> MCPPolicyDecision:
        if operation.startswith("secret.") and not self.secrets_allowed:
            return MCPPolicyDecision(False, reason="secrets are denied by default")
        if operation.startswith("fs."):
            return self._decide_filesystem(operation, target)
        if operation.startswith("network."):
            return self._decide_allow_list(target, self.network_allow, "network target is not allowed")
        if operation.startswith("command."):
            command = str(target).split()[0] if str(target).split() else str(target)
            return self._decide_allow_list(command, self.command_allow, "command is not allowed")
        return MCPPolicyDecision(True, reason="operation has no MCP policy restriction")

    def _decide_filesystem(self, operation: str, target: str) -> MCPPolicyDecision:
        normalized = _normalize_relative_path(target)
        if normalized is None:
            return MCPPolicyDecision(False, reason="path escapes project scope")
        if _matches_any(normalized, self.filesystem_deny):
            return MCPPolicyDecision(False, reason="path is explicitly denied")
        if self.filesystem_allow and not _matches_any(normalized, self.filesystem_allow):
            return MCPPolicyDecision(False, reason="path is outside filesystem allow-list")
        if operation != "fs.read":
            if self.write_mode == "read_only":
                return MCPPolicyDecision(False, reason="policy is read-only")
            if self.write_mode == "approval_required":
                return MCPPolicyDecision(False, requires_approval=True, reason="write requires approval")
        return MCPPolicyDecision(True, reason="allowed by filesystem policy")

    @staticmethod
    def _decide_allow_list(target: str, allowed: list[str], denied_reason: str) -> MCPPolicyDecision:
        if not allowed:
            return MCPPolicyDecision(False, reason=denied_reason)
        if str(target) in allowed:
            return MCPPolicyDecision(True, reason="allowed by allow-list")
        return MCPPolicyDecision(False, reason=denied_reason)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MCPPolicy":
        return cls(
            server_id=str(payload["server_id"]),
            filesystem_allow=list(payload.get("filesystem_allow") or []),
            filesystem_deny=list(payload.get("filesystem_deny") or []),
            network_allow=list(payload.get("network_allow") or []),
            command_allow=list(payload.get("command_allow") or []),
            secrets_allowed=bool(payload.get("secrets_allowed", False)),
            project_scope=str(payload.get("project_scope") or ""),
            write_mode=str(payload.get("write_mode") or "approval_required"),
        )


class MCPPolicyStore:
    """Persist MCP policies under the agent workspace."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "mcp" / "policies.json"

    def list(self) -> list[MCPPolicy]:
        policies = [MCPPolicy.from_dict(item) for item in self._read().get("policies", [])]
        return sorted(policies, key=lambda item: item.server_id)

    def get(self, server_id: str) -> MCPPolicy:
        for policy in self.list():
            if policy.server_id == server_id:
                return policy
        raise ConfigurationError(f"unknown MCP policy for server {server_id!r}")

    def set(self, policy: MCPPolicy) -> MCPPolicy:
        policies = [item for item in self.list() if item.server_id != policy.server_id]
        policies.append(policy)
        self._write(policies)
        return policy

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"policies": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, policies: list[MCPPolicy]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"policies": [policy.to_dict() for policy in sorted(policies, key=lambda item: item.server_id)]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_relative_path(target: str) -> str | None:
    path = PurePosixPath(str(target).replace("\\", "/"))
    if path.is_absolute():
        return None
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            return None
        parts.append(part)
    return "/".join(parts)


def _matches_any(path: str, prefixes: list[str]) -> bool:
    normalized_prefixes = [_normalize_relative_path(prefix) for prefix in prefixes]
    for prefix in normalized_prefixes:
        if prefix and (path == prefix or path.startswith(prefix.rstrip("/") + "/")):
            return True
    return False


__all__ = ["MCPPolicy", "MCPPolicyDecision", "MCPPolicyStore"]
