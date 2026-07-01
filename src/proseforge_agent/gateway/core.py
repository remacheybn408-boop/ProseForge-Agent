"""Messaging gateway core orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..agent import AgentKernel, AgentTurnRequest, IntentRouter
from ..chat import ChatSessionStore
from ..llm import FakeProvider
from ..chat.transcript import append_jsonl


@dataclass(frozen=True)
class MessageEvent:
    """Normalized inbound platform message."""

    platform: str
    chat_id: str
    user_id: str
    thread_id: str
    message_id: str
    text: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    authorization: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeliveryJob:
    """Append-only outbound delivery item."""

    platform: str
    chat_id: str
    thread_id: str
    text: str
    session_id: str
    reply_to_message_id: str = ""
    status: str = "queued"
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GatewayResult:
    """Outcome of handling one gateway event."""

    status: str
    session_id: str = ""
    delivery_jobs: list[DeliveryJob] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["delivery_jobs"] = [job.to_dict() for job in self.delivery_jobs]
        return data


class GatewayRunner:
    """Route platform events into agent turns and durable delivery jobs."""

    def __init__(
        self,
        root: str | Path = ".pf-agent",
        *,
        provider_name: str = "fake",
        allowed_users: set[str] | None = None,
        session_store: ChatSessionStore | None = None,
    ) -> None:
        self.root = Path(root)
        self.provider_name = provider_name
        self.allowed_users = set(allowed_users or [])
        self.session_store = session_store or ChatSessionStore(self.root)
        provider = FakeProvider(name=provider_name, model=provider_name)
        self.kernel = AgentKernel(
            provider=provider,
            session_store=self.session_store,
            intent_router=IntentRouter(),
        )
        self.delivery_queue_path = self.root / "gateway" / "deliveries.jsonl"

    def start(self, *, check: bool = False) -> GatewayResult:
        if check:
            return GatewayResult(status="ok", reason="gateway check mode")
        return GatewayResult(status="idle", reason="no platform adapter attached")

    def handle_event(self, event: MessageEvent) -> GatewayResult:
        if not self._authorized(event):
            return GatewayResult(status="denied", reason="user is not authorized")

        session_id = self.session_id_for(event)
        self.session_store.ensure_session(session_id, "general_chat", project_slug=None)
        result = self.kernel.run_turn(
            AgentTurnRequest(
                session_id=session_id,
                text=event.text,
                mode="general_chat",
                project_slug=None,
                permission_level="read_only",
            )
        )
        job = DeliveryJob(
            platform=event.platform,
            chat_id=event.chat_id,
            thread_id=event.thread_id,
            text=result.text,
            session_id=session_id,
            reply_to_message_id=event.message_id,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._append_delivery(job)
        return GatewayResult(status="queued", session_id=session_id, delivery_jobs=[job])

    def session_id_for(self, event: MessageEvent) -> str:
        parts = ["gateway", event.platform, event.chat_id, event.thread_id or "main"]
        return "_".join(_safe_part(part) for part in parts)

    def _authorized(self, event: MessageEvent) -> bool:
        if event.authorization.get("allowed") is True:
            return True
        return not self.allowed_users or event.user_id in self.allowed_users

    def _append_delivery(self, job: DeliveryJob) -> None:
        append_jsonl(self.delivery_queue_path, job.to_dict())


def _safe_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-")
    return cleaned or "unknown"
