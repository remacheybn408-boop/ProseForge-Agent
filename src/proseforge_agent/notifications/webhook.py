"""Webhook notification delivery channel."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Callable

from .core import NotificationEvent

WebhookTransport = Callable[[str, dict, dict, int], dict]
UrlResolver = Callable[[str], str]


class WebhookNotificationChannel:
    """Webhook channel with secret URL resolution, retry, timeout, and optional signing."""

    name = "webhook"

    def __init__(
        self,
        *,
        enabled: bool = True,
        url_ref: str = "",
        url_resolver: UrlResolver | None = None,
        events: list[str] | None = None,
        transport: WebhookTransport | None = None,
        retry_count: int = 2,
        timeout_seconds: int = 5,
        signing_secret: str = "",
        log_path: str | Path | None = None,
    ) -> None:
        self.enabled = enabled
        self.url_ref = url_ref
        self.url_resolver = url_resolver
        self.events = list(events or [])
        self.transport = transport
        self.retry_count = max(0, retry_count)
        self.timeout_seconds = timeout_seconds
        self.signing_secret = signing_secret
        self.log_path = Path(log_path) if log_path is not None else None

    def send(self, event: NotificationEvent) -> dict:
        if not self.enabled:
            return {"channel": self.name, "status": "skipped", "reason": "webhook disabled"}
        if self.events and event.event_type not in self.events:
            return {"channel": self.name, "status": "skipped", "reason": "event not subscribed"}
        if self.url_resolver is None or self.transport is None or not self.url_ref:
            return {"channel": self.name, "status": "unsupported", "reason": "webhook transport or URL resolver is not configured"}
        url = self.url_resolver(self.url_ref)
        payload = event.to_dict()
        headers = self._headers(payload)
        last_response: dict = {}
        for attempt in range(1, self.retry_count + 2):
            response = self.transport(url, payload, headers, self.timeout_seconds)
            last_response = response
            if response.get("ok"):
                return {"channel": self.name, "status": "sent", "attempts": attempt, "url_ref": self.url_ref}
            self._record_retry(event, attempt, response)
        return {
            "channel": self.name,
            "status": "failed",
            "attempts": self.retry_count + 1,
            "url_ref": self.url_ref,
            "last_status": last_response.get("status_code"),
        }

    def _headers(self, payload: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.signing_secret:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            signature = hmac.new(self.signing_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-ProseForge-Agent-Signature"] = signature
        return headers

    def _record_retry(self, event: NotificationEvent, attempt: int, response: dict) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event_id": event.id,
            "event_type": event.event_type,
            "attempt": attempt,
            "status_code": response.get("status_code"),
            "url_ref": self.url_ref,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = ["WebhookNotificationChannel"]
