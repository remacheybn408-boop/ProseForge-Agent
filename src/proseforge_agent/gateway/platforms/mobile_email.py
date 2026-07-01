"""Shared helpers for optional mobile/email adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import AdapterCapabilities, OutboundMessage, SendResult


@dataclass(frozen=True)
class GatewayAdapterCheck:
    status: str
    dry_run: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "dry_run": self.dry_run, "reason": self.reason}


class OptionalGatewayAdapter:
    platform = "optional"

    def __init__(self, *, api_key: str = "", max_message_size: int = 4000) -> None:
        self.api_key = api_key
        self.capabilities = AdapterCapabilities(
            threads=True,
            edits=False,
            reactions=False,
            attachments=True,
            max_message_size=max_message_size,
        )

    def send(self, message: OutboundMessage) -> SendResult:
        if len(message.text) > self.capabilities.max_message_size:
            return SendResult(delivered=False, retryable=True, reason="message exceeds adapter limit")
        return SendResult(
            delivered=True,
            retryable=False,
            message_ids=[f"{self.platform}-1"],
            raw_metadata={"api_key": "[redacted]", "recipient": "[redacted]"},
        )

    def edit(self, message: OutboundMessage) -> SendResult:
        return SendResult(delivered=False, retryable=False, reason="edits are not supported")

    def ack(self, event) -> SendResult:
        return SendResult(delivered=True, message_ids=[event.message_id])

    def health(self) -> dict[str, Any]:
        return {"platform": self.platform, "status": "ok", "api_key": "[redacted]"}

    def check(self, *, dry_run: bool = True) -> GatewayAdapterCheck:
        return GatewayAdapterCheck(
            status="ok",
            dry_run=dry_run,
            reason=f"{self.platform} adapter check uses fake transport",
        )


__all__ = ["GatewayAdapterCheck", "OptionalGatewayAdapter"]
