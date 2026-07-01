"""Vector store adapter tests (Task 134)."""

from __future__ import annotations

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.retrieval.embeddings import FakeEmbeddingProvider
from proseforge_agent.retrieval.vector_store import JsonlVectorStore, SqliteVectorStore, build_vector_store


def test_jsonl_vector_store_upsert_search_and_delete(tmp_path):
    embedder = FakeEmbeddingProvider(dimension=8)
    store = JsonlVectorStore(tmp_path / "vectors.jsonl")
    store.upsert("hero", embedder.embed_text("hero memory"), {"project_slug": "demo", "text": "hero memory"})
    store.upsert("villain", embedder.embed_text("villain memory"), {"project_slug": "demo", "text": "villain memory"})

    results = store.search(embedder.embed_text("hero memory"), top_k=1)

    assert results[0].id == "hero"
    assert results[0].metadata["text"] == "hero memory"
    assert results[0].score > 0.99
    store.delete("hero")
    assert [result.id for result in store.search(embedder.embed_text("hero memory"), top_k=5)] == ["villain"]


def test_sqlite_vector_store_matches_vector_store_contract(tmp_path):
    embedder = FakeEmbeddingProvider(dimension=6)
    store = SqliteVectorStore(tmp_path / "vectors.sqlite")
    store.upsert("chapter-1", embedder.embed_text("chapter one"), {"project_slug": "demo"})

    result = store.search(embedder.embed_text("chapter one"), top_k=1)[0]

    assert result.id == "chapter-1"
    assert result.metadata["project_slug"] == "demo"


def test_vector_store_factory_supports_local_and_rejects_reserved_adapters(tmp_path):
    assert isinstance(build_vector_store({"provider": "jsonl", "path": tmp_path / "vectors.jsonl"}), JsonlVectorStore)
    assert isinstance(build_vector_store({"provider": "sqlite", "path": tmp_path / "vectors.sqlite"}), SqliteVectorStore)

    with pytest.raises(ConfigurationError, match="not configured"):
        build_vector_store({"provider": "qdrant", "path": tmp_path / "unused"})
