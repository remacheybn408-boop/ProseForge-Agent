"""WhatsApp gateway adapter."""

from __future__ import annotations

from typing import Any, Iterable

from ..core import MessageEvent
from .mobile_email import OptionalGatewayAdapter


class WhatsAppGatewayAdapter(OptionalGatewayAdapter):
    platform = "whatsapp"

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        return iter(())

    def parse_event(self, payload: dict[str, Any]) -> MessageEvent:
        text = str(payload.get("body") or payload.get("text") or "")
        return MessageEvent(
            platform=self.platform,
            chat_id=str(payload.get("chat_id") or payload.get("from", "")),
            user_id=str(payload.get("from", "")),
            thread_id=str(payload.get("chat_id") or payload.get("from", "")),
            message_id=str(payload.get("message_id", "")),
            text=text,
            attachments=list(payload.get("attachments") or []),
            authorization={"allowed": True, "command": "stop" if text.strip().lower() in {"/stop", "stop"} else ""},
        )


__all__ = ["WhatsAppGatewayAdapter"]
