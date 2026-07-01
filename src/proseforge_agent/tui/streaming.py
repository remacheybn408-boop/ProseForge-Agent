"""Streaming tool output helpers for terminal surfaces."""

from __future__ import annotations

import re

from ..agent.events import EventBus, ToolOutputChunk


_SECRET_PATTERN = re.compile(r"\b(token|secret|password|api_key)=([^\s]+)", re.IGNORECASE)


class ToolOutputStreamer:
    """Emit bounded, redacted tool output chunks."""

    def __init__(
        self,
        *,
        tool_call_id: str,
        event_bus: EventBus | None = None,
        chunk_char_limit: int = 1024,
    ) -> None:
        self.tool_call_id = tool_call_id
        self.event_bus = event_bus
        self.chunk_char_limit = max(1, chunk_char_limit)
        self._sequence = 0

    def stream_text(self, text: str) -> list[ToolOutputChunk]:
        redacted_text, redacted = _redact_text(text)
        parts = [
            redacted_text[index : index + self.chunk_char_limit]
            for index in range(0, len(redacted_text), self.chunk_char_limit)
        ] or [""]
        chunks: list[ToolOutputChunk] = []
        for index, part in enumerate(parts):
            chunks.append(
                self._emit(
                    ToolOutputChunk(
                        tool_call_id=self.tool_call_id,
                        sequence=self._sequence,
                        text=part,
                        is_final=index == len(parts) - 1,
                        redacted=redacted,
                    )
                )
            )
            self._sequence += 1
        return chunks

    def stream_binary(self, payload: bytes) -> list[ToolOutputChunk]:
        return self.stream_text(f"[binary output: {len(payload)} bytes]")

    def cancel(self) -> ToolOutputChunk:
        chunk = ToolOutputChunk(
            tool_call_id=self.tool_call_id,
            sequence=self._sequence,
            text="",
            is_final=True,
            cancelled=True,
        )
        self._sequence += 1
        return self._emit(chunk)

    def _emit(self, chunk: ToolOutputChunk) -> ToolOutputChunk:
        if self.event_bus is not None:
            self.event_bus.emit("tool.output.chunk", chunk.to_dict())
        return chunk


def coalesce_chunks(chunks: list[ToolOutputChunk], *, char_limit: int | None = None) -> str:
    ordered = sorted(chunks, key=lambda chunk: chunk.sequence)
    text = "".join(chunk.text for chunk in ordered)
    if char_limit is None:
        return text
    return text[: max(0, char_limit)]


def _redact_text(text: str) -> tuple[str, bool]:
    redacted = _SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=[redacted]", text)
    return redacted, redacted != text


__all__ = ["ToolOutputStreamer", "coalesce_chunks"]
