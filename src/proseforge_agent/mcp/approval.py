"""MCP tool approval queue and gate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError
from .credentials import redact_sensitive
from .policy import MCPPolicy


_RISKY_TOOL_TOKENS = (
    "write",
    "delete",
    "remove",
    "overwrite",
    "config",
    "rules",
    "shell",
    "exec",
    "network",
    "fetch",
    "secret",
    "bulk",
)


@dataclass(frozen=True)
class MCPApprovalRequest:
    """One MCP tool call awaiting human approval."""

    id: str
    action: str
    status: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    decided_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MCPApprovalQueue:
    """Global queue for high-risk MCP tool calls."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "approvals" / "mcp_queue.json"

    def submit(self, *, server_id: str, tool_name: str, arguments: dict[str, Any]) -> MCPApprovalRequest:
        queue = self._load()
        queue["counter"] += 1
        request_id = f"approval_{queue['counter']:03d}"
        safe_arguments = redact_sensitive(arguments)
        summary = _summary(server_id, tool_name, safe_arguments)
        queue["requests"][request_id] = {
            "action": "mcp_tool_call",
            "status": "pending",
            "summary": summary,
            "payload": {
                "server_id": server_id,
                "tool_name": tool_name,
                "arguments": dict(safe_arguments),
            },
            "created_at": datetime.now(UTC).isoformat(),
            "decided_at": "",
        }
        self._save(queue)
        return self._request(request_id, queue["requests"][request_id])

    def list(self, status: str | None = None) -> list[MCPApprovalRequest]:
        queue = self._load()
        requests = [
            self._request(request_id, payload)
            for request_id, payload in queue["requests"].items()
            if status is None or payload.get("status") == status
        ]
        return sorted(requests, key=lambda request: _request_number(request.id))

    def show(self, approval_id: str) -> MCPApprovalRequest:
        queue = self._load()
        payload = queue["requests"].get(approval_id)
        if payload is None:
            raise ConfigurationError(f"approval {approval_id!r} not found")
        return self._request(approval_id, payload)

    def approve(self, approval_id: str) -> MCPApprovalRequest:
        return self._decide(approval_id, "approved")

    def reject(self, approval_id: str) -> MCPApprovalRequest:
        return self._decide(approval_id, "rejected")

    def _decide(self, approval_id: str, status: str) -> MCPApprovalRequest:
        queue = self._load()
        payload = queue["requests"].get(approval_id)
        if payload is None:
            raise ConfigurationError(f"approval {approval_id!r} not found")
        if payload.get("status") != "pending":
            raise ConfigurationError(f"approval {approval_id!r} is already {payload.get('status')}")
        payload["status"] = status
        payload["decided_at"] = datetime.now(UTC).isoformat()
        self._save(queue)
        return self._request(approval_id, payload)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"counter": 0, "requests": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, queue: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _request(request_id: str, payload: dict[str, Any]) -> MCPApprovalRequest:
        return MCPApprovalRequest(
            id=request_id,
            action=str(payload.get("action", "")),
            status=str(payload.get("status", "")),
            summary=str(payload.get("summary", "")),
            payload=dict(payload.get("payload") or {}),
            created_at=str(payload.get("created_at", "")),
            decided_at=str(payload.get("decided_at", "")),
        )


class MCPApprovalGate:
    """Route high-risk MCP calls into the approval queue before execution."""

    def __init__(self, *, queue: MCPApprovalQueue, known_tools: set[str] | None = None) -> None:
        self.queue = queue
        self.known_tools = set(known_tools or set())

    def enqueue_if_required(
        self,
        *,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        policy: MCPPolicy,
    ) -> MCPApprovalRequest | None:
        if not self._requires_approval(tool_name, arguments, policy):
            return None
        return self.queue.submit(server_id=server_id, tool_name=tool_name, arguments=arguments)

    def _requires_approval(self, tool_name: str, arguments: dict[str, Any], policy: MCPPolicy) -> bool:
        if self.known_tools and tool_name not in self.known_tools:
            return True
        lowered = tool_name.lower()
        if any(token in lowered for token in _RISKY_TOOL_TOKENS):
            return True
        target = str(arguments.get("path") or arguments.get("target") or "")
        if target:
            operation = "fs.write" if any(token in lowered for token in ("write", "delete", "remove", "overwrite")) else "fs.read"
            decision = policy.decide(operation, target)
            if decision.requires_approval or not decision.allowed:
                return True
        return False


def _summary(server_id: str, tool_name: str, arguments: dict[str, Any]) -> str:
    target = arguments.get("path") or arguments.get("target") or arguments.get("url") or ""
    return f"MCP tool wants approval: server={server_id} tool={tool_name} target={target}"


def _request_number(request_id: str) -> int:
    try:
        return int(request_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0


__all__ = ["MCPApprovalGate", "MCPApprovalQueue", "MCPApprovalRequest"]
