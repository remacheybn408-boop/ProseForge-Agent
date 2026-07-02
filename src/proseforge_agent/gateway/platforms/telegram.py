"""Telegram gateway adapter with deterministic fake transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ..core import MessageEvent
from .base import AdapterCapabilities, OutboundMessage, SendResult, fake_transport_refusal


@dataclass(frozen=True)
class TelegramCheckResult:
    status: str
    dry_run: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "dry_run": self.dry_run, "reason": self.reason}


class TelegramGatewayAdapter:
    """Optional Telegram adapter backed by injected/fake transport in tests."""

    platform = "telegram"

    def __init__(self, *, token: str = "", max_message_size: int = 4096, allow_fake_transport: bool = False) -> None:
        self.token = token
        self.allow_fake_transport = allow_fake_transport
        self.capabilities = AdapterCapabilities(
            threads=True,
            edits=True,
            reactions=False,
            attachments=True,
            max_message_size=max_message_size,
        )

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        return iter(())

    def parse_update(self, update: dict[str, Any]) -> MessageEvent:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        sender = message.get("from") or {}
        text = str(message.get("text") or "")
        authorization = {"allowed": True}
        if text.strip().lower() == "/stop":
            authorization["command"] = "stop"
        return MessageEvent(
            platform=self.platform,
            chat_id=str(chat.get("id", "")),
            user_id=str(sender.get("id", "")),
            thread_id=str(message.get("message_thread_id") or ""),
            message_id=str(message.get("message_id", "")),
            text=text,
            attachments=_attachment_refs(message),
            authorization=authorization,
        )

    def send(self, message: OutboundMessage) -> SendResult:
        refusal = fake_transport_refusal(self.platform, self.allow_fake_transport)
        if refusal is not None:
            return refusal
        chunks = _chunk_text(message.text, self.capabilities.max_message_size)
        message_ids = [f"telegram-{index + 1}" for index, _ in enumerate(chunks)]
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=message_ids,
            continuation_ids=message_ids[1:],
            raw_metadata={"token": "[redacted]", "chat_id": "[redacted]", "chunks": len(chunks)},
        )

    def edit(self, message: OutboundMessage) -> SendResult:
        refusal = fake_transport_refusal(self.platform, self.allow_fake_transport)
        if refusal is not None:
            return refusal
        if not message.message_id:
            return SendResult(delivered=False, retryable=False, reason="message_id is required for edit")
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=[message.message_id],
            raw_metadata={"token": "[redacted]", "chat_id": "[redacted]"},
        )

    def ack(self, event: MessageEvent) -> SendResult:
        return SendResult(delivered=True, message_ids=[event.message_id])

    def health(self) -> dict[str, Any]:
        return {"platform": self.platform, "status": "ok", "token": "[redacted]"}

    def check(self, *, dry_run: bool = True) -> TelegramCheckResult:
        return TelegramCheckResult(status="ok", dry_run=dry_run, reason="telegram adapter check uses fake transport")


def _chunk_text(text: str, limit: int) -> list[str]:
    limit = max(1, limit)
    return [text[index : index + limit] for index in range(0, len(text), limit)] or [""]


def _attachment_refs(message: dict[str, Any]) -> list[dict[str, Any]]:
    attachments: list[dict[str, Any]] = []
    for key in ("photo", "document", "audio", "video"):
        if key in message:
            attachments.append({"type": key, "metadata": message[key]})
    return attachments


__all__ = ["TelegramCheckResult", "TelegramGatewayAdapter"]
