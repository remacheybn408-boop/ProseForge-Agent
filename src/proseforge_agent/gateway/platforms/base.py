"""Base contract for messaging platform adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Protocol

from ..core import MessageEvent


_SENSITIVE_KEY_PARTS = ("token", "secret", "password", "authorization", "api_key")


@dataclass(frozen=True)
class AdapterCapabilities:
    threads: bool = False
    edits: bool = False
    reactions: bool = False
    attachments: bool = False
    max_message_size: int = 4000

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OutboundMessage:
    platform: str
    chat_id: str
    thread_id: str
    text: str
    message_id: str = ""
    continuation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SendResult:
    delivered: bool
    retryable: bool = False
    message_ids: list[str] = field(default_factory=list)
    continuation_ids: list[str] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PlatformAdapter(Protocol):
    platform: str
    capabilities: AdapterCapabilities

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        ...

    def send(self, message: OutboundMessage) -> SendResult:
        ...

    def edit(self, message: OutboundMessage) -> SendResult:
        ...

    def ack(self, event: MessageEvent) -> SendResult:
        ...

    def health(self) -> dict[str, Any]:
        ...


class FakePlatformAdapter:
    """Deterministic platform adapter for gateway tests."""

    platform = "fake"

    def __init__(self, inbound: list[dict[str, Any]] | None = None, *, max_message_size: int = 4000) -> None:
        self._inbound = list(inbound or [])
        self.capabilities = AdapterCapabilities(
            threads=True,
            edits=True,
            reactions=True,
            attachments=True,
            max_message_size=max_message_size,
        )
        self._counter = 0

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        for row in self._inbound:
            yield MessageEvent(
                platform=self.platform,
                chat_id=str(row.get("chat_id", "")),
                user_id=str(row.get("user_id", "")),
                thread_id=str(row.get("thread_id", "")),
                message_id=str(row.get("message_id", "")),
                text=str(row.get("text", "")),
                attachments=list(row.get("attachments") or []),
                authorization={"allowed": True, "raw": _redact(row.get("raw") or {})},
            )

    def send(self, message: OutboundMessage) -> SendResult:
        if len(message.text) > self.capabilities.max_message_size:
            return SendResult(
                delivered=False,
                retryable=False,
                reason=f"message exceeds max message size {self.capabilities.max_message_size}",
            )
        self._counter += 1
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=[f"fake-{self._counter}"],
            raw_metadata=_redact({"platform": self.platform, "token": "fake-token"}),
        )

    def edit(self, message: OutboundMessage) -> SendResult:
        if not self.capabilities.edits:
            return SendResult(delivered=False, retryable=False, reason="edits are not supported")
        return SendResult(delivered=True, message_ids=[message.message_id or "fake-edited"])

    def ack(self, event: MessageEvent) -> SendResult:
        return SendResult(delivered=True, message_ids=[event.message_id])

    def health(self) -> dict[str, Any]:
        return {"platform": self.platform, "status": "ok", "capabilities": self.capabilities.to_dict()}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            lowered = str(key).lower()
            redacted[key] = "[redacted]" if any(part in lowered for part in _SENSITIVE_KEY_PARTS) else _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


__all__ = ["AdapterCapabilities", "FakePlatformAdapter", "OutboundMessage", "PlatformAdapter", "SendResult"]
