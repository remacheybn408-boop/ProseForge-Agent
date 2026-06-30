"""Human approval queue: gate high-risk actions behind explicit human decisions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APPROVALS_DIR = "approvals"
QUEUE_NAME = "queue.json"

# Actions that must never run autonomously; they enqueue for human review instead.
HIGH_RISK_ACTIONS = (
    "overwrite_draft",
    "delete_artifact",
    "accept_canon_change",
    "resolve_conflict",
    "bulk_reorder",
    "export_final",
    "rollback_version",
    "modify_global_rules",
)

_DECISION_STATUS = {"approve": "approved", "reject": "rejected"}


@dataclass(frozen=True)
class ApprovalRequest:
    """One queued high-risk action awaiting a human decision."""

    id: str
    action: str
    status: str
    summary: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    decided_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApprovalQueue:
    """Queue high-risk actions so the agent cannot damage the manuscript on its own."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.queue_path = self.project_root / APPROVALS_DIR / QUEUE_NAME

    def submit(self, action: str, *, summary: str = "", payload: dict[str, Any] | None = None) -> ApprovalRequest:
        if action not in HIGH_RISK_ACTIONS:
            raise ValueError(f"action {action!r} is not a high-risk action requiring approval")
        queue = self._load()
        queue["counter"] += 1
        request_id = f"approval_{queue['counter']:03d}"
        queue["requests"][request_id] = {
            "action": action,
            "status": "pending",
            "summary": summary,
            "payload": dict(payload or {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "decided_at": "",
        }
        self._save(queue)
        return self._request(request_id, queue["requests"][request_id])

    def list(self, status: str | None = None) -> list[ApprovalRequest]:
        queue = self._load()
        items = [
            self._request(request_id, entry)
            for request_id, entry in queue["requests"].items()
            if status is None or entry["status"] == status
        ]
        items.sort(key=lambda request: _request_number(request.id))
        return items

    def show(self, approval_id: str) -> ApprovalRequest:
        queue = self._load()
        entry = queue["requests"].get(approval_id)
        if entry is None:
            raise ValueError(f"approval {approval_id!r} not found")
        return self._request(approval_id, entry)

    def approve(self, approval_id: str) -> ApprovalRequest:
        return self._decide(approval_id, "approve")

    def reject(self, approval_id: str) -> ApprovalRequest:
        return self._decide(approval_id, "reject")

    # -- internals -------------------------------------------------------

    def _decide(self, approval_id: str, decision: str) -> ApprovalRequest:
        queue = self._load()
        entry = queue["requests"].get(approval_id)
        if entry is None:
            raise ValueError(f"approval {approval_id!r} not found")
        if entry["status"] != "pending":
            raise ValueError(f"approval {approval_id!r} is already {entry['status']}")
        entry["status"] = _DECISION_STATUS[decision]
        entry["decided_at"] = datetime.now(timezone.utc).isoformat()
        self._save(queue)
        return self._request(approval_id, entry)

    def _load(self) -> dict[str, Any]:
        if self.queue_path.exists():
            return json.loads(self.queue_path.read_text(encoding="utf-8"))
        return {"counter": 0, "requests": {}}

    def _save(self, queue: dict[str, Any]) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        self.queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")

    def _request(self, request_id: str, entry: dict[str, Any]) -> ApprovalRequest:
        return ApprovalRequest(
            id=request_id,
            action=entry["action"],
            status=entry["status"],
            summary=entry.get("summary", ""),
            payload=dict(entry.get("payload", {})),
            created_at=entry.get("created_at", ""),
            decided_at=entry.get("decided_at", ""),
        )


def _request_number(request_id: str) -> int:
    try:
        return int(request_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0


__all__ = ["APPROVALS_DIR", "HIGH_RISK_ACTIONS", "ApprovalQueue", "ApprovalRequest"]
