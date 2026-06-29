"""Deterministic fake provider.

Every workflow must run offline before any real model API is introduced. The
fake provider needs no network and no API key, and produces the same output
for the same request so tests and golden snapshots are stable.
"""

from __future__ import annotations

from collections.abc import Iterator

from .base import Message, ProviderRequest, ProviderResult, StreamChunk, Usage


def _last_user_text(messages: list[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return messages[-1].content if messages else ""


def _word_count(text: str) -> int:
    return len(text.split())


class FakeProvider:
    """A deterministic, offline stand-in for a real model provider."""

    def __init__(self, name: str, model: str) -> None:
        self.name = name
        self.model = model

    def _render(self, request: ProviderRequest) -> str:
        echo = _last_user_text(request.messages)
        return f"[fake:{self.model}] role={request.role} :: {echo}"

    def generate(self, request: ProviderRequest) -> ProviderResult:
        text = self._render(request)
        prompt_tokens = sum(_word_count(m.content) for m in request.messages)
        usage = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=_word_count(text),
        )
        return ProviderResult(
            provider=self.name,
            model=self.model,
            text=text,
            usage=usage,
            raw={"deterministic": True},
        )

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]:
        text = self._render(request)
        # Split into whitespace-preserving chunks so the joined stream is
        # byte-for-byte identical to generate().text.
        parts = text.split(" ")
        for index, part in enumerate(parts):
            piece = part if index == len(parts) - 1 else part + " "
            yield StreamChunk(text=piece, done=index == len(parts) - 1, index=index)


__all__ = ["FakeProvider"]
