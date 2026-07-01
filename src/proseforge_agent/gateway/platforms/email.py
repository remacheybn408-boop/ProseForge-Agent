"""Email gateway adapter."""

from __future__ import annotations

from typing import Any, Iterable

from ..core import MessageEvent
from .mobile_email import OptionalGatewayAdapter


class EmailGatewayAdapter(OptionalGatewayAdapter):
    platform = "email"

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        return iter(())

    def parse_event(self, payload: dict[str, Any]) -> MessageEvent:
        subject = str(payload.get("subject") or "")
        body = str(payload.get("body") or "")
        text = f"{subject}\n{body}".strip()
        return MessageEvent(
            platform=self.platform,
            chat_id=str(payload.get("from", "")),
            user_id=str(payload.get("from", "")),
            thread_id=str(payload.get("thread_id") or payload.get("message_id", "")),
            message_id=str(payload.get("message_id", "")),
            text=text,
            attachments=list(payload.get("attachments") or []),
            authorization={"allowed": True, "command": "stop" if body.strip().lower() in {"/stop", "stop", "unsubscribe"} else ""},
        )


__all__ = ["EmailGatewayAdapter"]
