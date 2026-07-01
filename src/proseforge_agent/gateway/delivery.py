"""Reliable delivery helpers for gateway adapters."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from .platforms.base import OutboundMessage, PlatformAdapter


@dataclass(frozen=True)
class DeliveryResult:
    """Final accounting for a gateway delivery attempt."""

    session_key: str
    delivered: bool
    chunk_count: int
    continuation_ids: list[str] = field(default_factory=list)
    message_ids: list[str] = field(default_factory=list)
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)
    duplicate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DeliveryManager:
    """Chunk, retry, and account for adapter delivery."""

    def __init__(self, *, adapter: PlatformAdapter, max_retries: int = 2) -> None:
        self.adapter = adapter
        self.max_retries = max(0, max_retries)
        self._delivered_keys: dict[str, DeliveryResult] = {}

    def deliver(self, session_key: str, outbound_message: OutboundMessage) -> DeliveryResult:
        dedupe_key = self._dedupe_key(session_key, outbound_message)
        if dedupe_key in self._delivered_keys:
            prior = self._delivered_keys[dedupe_key]
            return DeliveryResult(
                session_key=prior.session_key,
                delivered=prior.delivered,
                chunk_count=prior.chunk_count,
                continuation_ids=list(prior.continuation_ids),
                message_ids=list(prior.message_ids),
                retry_count=prior.retry_count,
                errors=list(prior.errors),
                duplicate=True,
            )

        chunks = _chunk_text(outbound_message.text, self.adapter.capabilities.max_message_size)
        continuation_ids: list[str] = []
        message_ids: list[str] = []
        errors: list[str] = []
        retry_count = 0
        all_delivered = True
        for index, chunk in enumerate(chunks):
            continuation_id = f"{session_key}-{index}"
            attempt = 0
            while True:
                chunk_message = OutboundMessage(
                    platform=outbound_message.platform,
                    chat_id=outbound_message.chat_id,
                    thread_id=outbound_message.thread_id,
                    text=chunk,
                    message_id=outbound_message.message_id,
                    continuation_id=continuation_id,
                )
                send_result = self.adapter.send(chunk_message)
                if send_result.delivered:
                    continuation_ids.extend(send_result.continuation_ids or [continuation_id])
                    message_ids.extend(send_result.message_ids)
                    break
                if send_result.retryable and attempt < self.max_retries:
                    attempt += 1
                    retry_count += 1
                    continue
                all_delivered = False
                if send_result.reason:
                    errors.append(_redact_text(send_result.reason))
                break

        result = DeliveryResult(
            session_key=session_key,
            delivered=all_delivered and len(continuation_ids) == len(chunks),
            chunk_count=len(chunks),
            continuation_ids=continuation_ids,
            message_ids=message_ids,
            retry_count=retry_count,
            errors=errors,
        )
        if result.delivered:
            self._delivered_keys[dedupe_key] = result
        return result

    @staticmethod
    def _dedupe_key(session_key: str, message: OutboundMessage) -> str:
        payload = "|".join([session_key, message.platform, message.chat_id, message.thread_id, message.text])
        return sha256(payload.encode("utf-8")).hexdigest()


def _chunk_text(text: str, limit: int) -> list[str]:
    limit = max(1, limit)
    return [text[index : index + limit] for index in range(0, len(text), limit)] or [""]


def _redact_text(text: str) -> str:
    return re.sub(
        r"(?i)\b(token|secret|password|api_key)=([^\s]+)",
        lambda match: f"{match.group(1)}=[redacted]",
        text,
    )


__all__ = ["DeliveryManager", "DeliveryResult"]
