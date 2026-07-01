"""Embeddings abstraction tests (Task 133)."""

from __future__ import annotations

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.retrieval.embeddings import (
    EmbeddingConfig,
    FakeEmbeddingProvider,
    build_embedding_provider,
)


def test_fake_embedding_provider_returns_stable_dimension_vectors():
    provider = FakeEmbeddingProvider(dimension=8)

    first = provider.embed_text("same text")
    second = provider.embed_text("same text")
    other = provider.embed_text("different text")

    assert len(first) == 8
    assert first == second
    assert first != other
    assert all(isinstance(value, float) for value in first)


def test_embedding_provider_batch_matches_single_calls():
    provider = FakeEmbeddingProvider(dimension=6)
    texts = ["alpha", "beta"]

    assert provider.embed_batch(texts) == [provider.embed_text(text) for text in texts]


def test_embedding_provider_factory_supports_fake_and_rejects_unconfigured_remote():
    fake = build_embedding_provider(EmbeddingConfig(provider="fake", dimension=4))
    assert fake.embed_text("hello")

    with pytest.raises(ConfigurationError, match="not configured"):
        build_embedding_provider(EmbeddingConfig(provider="openai", dimension=4))
