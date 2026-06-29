"""Uniform streaming channel with a non-streaming fallback.

Providers that support streaming yield :class:`StreamChunk` pieces from
``generate_stream``. Providers that only implement ``generate`` are adapted by
:class:`NonStreamingAdapter` to yield a single terminal chunk, so callers never
have to special-case streaming support.

The aggregated stream text always equals the non-streaming ``generate`` result,
so transcripts and memory extraction are unaffected by whether a turn streamed.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Protocol, runtime_checkable

from .base import ProviderRequest, ProviderResult, StreamChunk


@runtime_checkable
class StreamingProvider(Protocol):
    """A provider exposing both a one-shot and a streaming generation channel."""

    name: str
    model: str

    def generate(self, request: ProviderRequest) -> ProviderResult: ...

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]: ...


class NonStreamingAdapter:
    """Adapt a ``generate``-only provider into the streaming contract.

    ``generate_stream`` yields exactly one terminal chunk (``done=True``) wrapping
    the full non-streaming text, so downstream consumers stay uniform.
    """

    def __init__(self, provider) -> None:
        self._provider = provider
        self.name = getattr(provider, "name", "")
        self.model = getattr(provider, "model", "")

    def generate(self, request: ProviderRequest) -> ProviderResult:
        return self._provider.generate(request)

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]:
        result = self._provider.generate(request)
        yield StreamChunk(text=result.text, done=True, index=0)


def supports_streaming(provider) -> bool:
    """True if ``provider`` implements its own ``generate_stream``."""
    return callable(getattr(provider, "generate_stream", None))


def as_streaming(provider) -> StreamingProvider:
    """Return ``provider`` unchanged if it streams, else wrap it for fallback."""
    if supports_streaming(provider):
        return provider
    return NonStreamingAdapter(provider)


def iter_stream(provider, request: ProviderRequest) -> Iterator[StreamChunk]:
    """Yield ordered :class:`StreamChunk` pieces for any provider."""
    yield from as_streaming(provider).generate_stream(request)


def aggregate_text(chunks: Iterable[StreamChunk]) -> str:
    """Join chunk text in order; equals the non-streaming ``generate`` text."""
    return "".join(chunk.text for chunk in chunks)


__all__ = [
    "StreamingProvider",
    "NonStreamingAdapter",
    "supports_streaming",
    "as_streaming",
    "iter_stream",
    "aggregate_text",
]
