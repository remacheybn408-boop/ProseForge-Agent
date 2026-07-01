"""Signal gateway adapter."""

from __future__ import annotations

from typing import Any, Iterable

from ..core import MessageEvent
from .mobile_email import OptionalGatewayAdapter


class SignalGatewayAdapter(OptionalGatewayAdapter):
    platform = "signal"

    def poll_or_listen(self) -> Iterable[MessageEvent]:
        return iter(())

    def parse_event(self, payload: dict[str, Any]) -> MessageEvent:
        text = str(payload.get("message") or payload.get("text") or "")
        return MessageEvent(
            platform=self.platform,
            chat_id=str(payload.get("group_id") or payload.get("source", "")),
            user_id=str(payload.get("source", "")),
            thread_id=str(payload.get("group_id") or payload.get("source", "")),
            message_id=str(payload.get("timestamp", "")),
            text=text,
            attachments=list(payload.get("attachments") or []),
            authorization={"allowed": True, "command": "stop" if text.strip().lower() in {"/stop", "stop"} else ""},
        )


__all__ = ["SignalGatewayAdapter"]
