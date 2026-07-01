"""Provider-neutral embedding abstraction for retrieval."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from ..errors import ConfigurationError


class EmbeddingProvider(Protocol):
    """Minimal provider contract used by vector retrieval."""

    dimension: int

    def embed_text(self, text: str) -> list[float]:
        """Embed one text into a fixed-size vector."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts in input order."""


@dataclass(frozen=True)
class EmbeddingConfig:
    """Embedding provider configuration."""

    provider: str = "fake"
    dimension: int = 384
    model: str = ""
    endpoint: str = ""
    api_key: str = ""


class FakeEmbeddingProvider:
    """Deterministic, dependency-free embedding provider for tests and offline use."""

    def __init__(self, *, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ConfigurationError("embedding dimension must be positive")
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < self.dimension:
            digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
            values.extend((byte / 255.0) * 2.0 - 1.0 for byte in digest)
            counter += 1
        return values[: self.dimension]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def build_embedding_provider(config: EmbeddingConfig | dict | None = None) -> EmbeddingProvider:
    """Build an embedding provider without performing network calls."""
    if config is None:
        config = EmbeddingConfig()
    if isinstance(config, dict):
        config = EmbeddingConfig(**config)
    provider = config.provider.lower().replace("-", "_")
    if provider == "fake":
        return FakeEmbeddingProvider(dimension=config.dimension)
    if provider in {"local", "sentence_transformers", "openai", "qwen", "custom_http"}:
        raise ConfigurationError(f"{config.provider} embedding provider is not configured")
    raise ConfigurationError(f"unknown embedding provider: {config.provider}")


__all__ = ["EmbeddingConfig", "EmbeddingProvider", "FakeEmbeddingProvider", "build_embedding_provider"]
