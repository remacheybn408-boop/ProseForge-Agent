"""Discord gateway adapter with fake-client semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ..core import MessageEvent
from .base import AdapterCapabilities, OutboundMessage, SendResult, fake_transport_refusal


@dataclass(frozen=True)
class DiscordCheckResult:
    status: str
    dry_run: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "dry_run": self.dry_run, "reason": self.reason}


class DiscordGatewayAdapter:
    platform = "discord"

    def __init__(self, *, token: str = "", max_message_size: int = 2000, allow_fake_transport: bool = False) -> None:
        self.token = token
        self.allow_fake_transport = allow_fake_transport
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
        author = payload.get("author") or {}
        text = str(payload.get("content") or "")
        return MessageEvent(
            platform=self.platform,
            chat_id=str(payload.get("channel_id", "")),
            user_id=str(author.get("id", "")),
            thread_id=str(payload.get("thread_id") or payload.get("channel_id", "")),
            message_id=str(payload.get("id", "")),
            text=text,
            attachments=list(payload.get("attachments") or []),
            authorization={"allowed": True, "command": "stop" if text.strip().lower() in {"/stop", "stop"} else ""},
        )

    def send(self, message: OutboundMessage) -> SendResult:
        refusal = fake_transport_refusal(self.platform, self.allow_fake_transport)
        if refusal is not None:
            return refusal
        if len(message.text) > self.capabilities.max_message_size:
            return SendResult(delivered=False, retryable=True, reason="discord rate/size limit requires retry or chunking")
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=["discord-1"],
            raw_metadata={"token": "[redacted]", "channel_id": "[redacted]"},
        )

    def edit(self, message: OutboundMessage) -> SendResult:
        refusal = fake_transport_refusal(self.platform, self.allow_fake_transport)
        if refusal is not None:
            return refusal
        return SendResult(delivered=bool(message.message_id), message_ids=[message.message_id] if message.message_id else [], reason="" if message.message_id else "message_id is required")

    def ack(self, event: MessageEvent) -> SendResult:
        return SendResult(delivered=True, message_ids=[event.message_id])

    def health(self) -> dict[str, Any]:
        return {"platform": self.platform, "status": "ok", "token": "[redacted]"}

    def check(self, *, dry_run: bool = True) -> DiscordCheckResult:
        return DiscordCheckResult(status="ok", dry_run=dry_run, reason="discord adapter check uses fake transport")


__all__ = ["DiscordCheckResult", "DiscordGatewayAdapter"]
