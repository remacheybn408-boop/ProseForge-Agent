"""Normalized provider contract.

These are the only provider-facing types workflows depend on. Concrete
providers (fake, OpenAI-compatible, native) implement :class:`LLMProvider`
and return a :class:`ProviderResult`, so workflow code never branches on the
underlying API shape.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

STANDARD_ROLES: tuple[str, ...] = ("planner", "drafter", "critic", "reviser", "memory")


@dataclass(frozen=True)
class Message:
    """One chat message in a provider request."""

    role: str
    content: str


@dataclass(frozen=True)
class ProviderRequest:
    """A role-tagged generation request, independent of any provider API."""

    role: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass(frozen=True)
class Usage:
    """Token accounting for a single generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class ProviderResult:
    """Normalized generation result returned to workflows."""

    provider: str
    model: str
    text: str
    usage: Usage = field(default_factory=Usage)
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StreamChunk:
    """One incremental piece of a streamed generation."""

    text: str
    done: bool = False
    index: int = 0


@dataclass(frozen=True)
class ProviderSpec:
    """Declarative description of one configured provider."""

    name: str
    kind: str
    model: str
    options: dict = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol every concrete provider implements."""

    name: str
    model: str

    def generate(self, request: ProviderRequest) -> ProviderResult: ...

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]: ...


__all__ = [
    "STANDARD_ROLES",
    "Message",
    "ProviderRequest",
    "Usage",
    "ProviderResult",
    "StreamChunk",
    "ProviderSpec",
    "LLMProvider",
]
