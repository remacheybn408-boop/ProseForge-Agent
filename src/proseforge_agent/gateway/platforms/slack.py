"""Slack gateway adapter with fake-client semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ..core import MessageEvent
from .base import AdapterCapabilities, OutboundMessage, SendResult


@dataclass(frozen=True)
class SlackCheckResult:
    status: str
    dry_run: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "dry_run": self.dry_run, "reason": self.reason}


class SlackGatewayAdapter:
    platform = "slack"

    def __init__(self, *, token: str = "", max_message_size: int = 40000) -> None:
        self.token = token
        self.capabilities = AdapterCapabilities(
            threads=True,
            edits=True,
            reactions=True,
            attachments=True,
            max_message_size=max_message_size,
        )

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        return iter(())

    def parse_event(self, payload: dict[str, Any]) -> MessageEvent:
        text = str(payload.get("text") or "")
        return MessageEvent(
            platform=self.platform,
            chat_id=str(payload.get("channel", "")),
            user_id=str(payload.get("user", "")),
            thread_id=str(payload.get("thread_ts") or payload.get("ts", "")),
            message_id=str(payload.get("ts", "")),
            text=text,
            attachments=list(payload.get("files") or []),
            authorization={"allowed": True, "command": "stop" if text.strip().lower() in {"/stop", "stop"} else ""},
        )

    def send(self, message: OutboundMessage) -> SendResult:
        if len(message.text) > self.capabilities.max_message_size:
            return SendResult(delivered=False, retryable=True, reason="slack rate/size limit requires retry or chunking")
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=["slack-1"],
            raw_metadata={"token": "[redacted]", "channel": "[redacted]"},
        )

    def edit(self, message: OutboundMessage) -> SendResult:
        return SendResult(delivered=bool(message.message_id), message_ids=[message.message_id] if message.message_id else [], reason="" if message.message_id else "message_id is required")

    def ack(self, event: MessageEvent) -> SendResult:
        return SendResult(delivered=True, message_ids=[event.message_id])

    def health(self) -> dict[str, Any]:
        return {"platform": self.platform, "status": "ok", "token": "[redacted]"}

    def check(self, *, dry_run: bool = True) -> SlackCheckResult:
        return SlackCheckResult(status="ok", dry_run=dry_run, reason="slack adapter check uses fake transport")


__all__ = ["SlackCheckResult", "SlackGatewayAdapter"]
