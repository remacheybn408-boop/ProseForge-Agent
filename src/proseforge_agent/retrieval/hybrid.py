"""Hybrid keyword and vector retrieval."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .embeddings import EmbeddingProvider, FakeEmbeddingProvider
from .vector_store import InMemoryVectorStore, VectorStore


@dataclass(frozen=True)
class RagDocument:
    """One searchable RAG document or chunk."""

    id: str
    text: str
    project_slug: str
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict) -> "RagDocument":
        metadata = dict(payload.get("metadata") or {})
        return cls(
            id=str(payload["id"]),
            text=str(payload.get("text", "")),
            project_slug=str(payload.get("project_slug") or metadata.get("project_slug") or ""),
            metadata=metadata,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class HybridSearchResult:
    """One hybrid search result with score components."""

    id: str
    text: str
    project_slug: str
    metadata: dict
    score: float
    keyword_score: float
    vector_score: float
    channels: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class HybridRetriever:
    """Combine keyword and vector similarity with project scope filtering."""

    def __init__(
        self,
        documents: list[RagDocument],
        *,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.documents = list(documents)
        self.embedding_provider = embedding_provider or FakeEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()
        for document in self.documents:
            self.vector_store.upsert(
                document.id,
                self.embedding_provider.embed_text(document.text),
                {
                    "project_slug": document.project_slug,
                    "text": document.text,
                    **document.metadata,
                },
            )

    def search(self, query: str, *, project_slug: str, top_k: int = 5, metadata_filter: dict | None = None) -> list[HybridSearchResult]:
        metadata_filter = dict(metadata_filter or {})
        vector_hits = {
            hit.id: hit.score
            for hit in self.vector_store.search(self.embedding_provider.embed_text(query), top_k=max(top_k, len(self.documents)))
        }
        results: list[HybridSearchResult] = []
        for document in self.documents:
            if document.project_slug != project_slug:
                continue
            if any(document.metadata.get(key) != value for key, value in metadata_filter.items()):
                continue
            keyword_score = _keyword_score(query, document.text, document.metadata)
            vector_score = vector_hits.get(document.id, 0.0)
            channels = []
            if keyword_score > 0:
                channels.append("keyword")
            if vector_score > 0:
                channels.append("vector")
            if not channels:
                continue
            score = keyword_score + vector_score
            results.append(
                HybridSearchResult(
                    id=document.id,
                    text=document.text,
                    project_slug=document.project_slug,
                    metadata=dict(document.metadata),
                    score=score,
                    keyword_score=keyword_score,
                    vector_score=vector_score,
                    channels=channels,
                )
            )
        results.sort(key=lambda item: (-item.score, item.id))
        return results[: max(0, top_k)]


def load_rag_documents(path: str | Path) -> list[RagDocument]:
    """Load RAG documents from a JSONL chunk file."""
    file_path = Path(path)
    if not file_path.exists():
        return []
    documents: list[RagDocument] = []
    for line in file_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            documents.append(RagDocument.from_dict(payload))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return documents


def _keyword_score(query: str, text: str, metadata: dict) -> float:
    haystack = " ".join([text, *[str(value) for value in metadata.values()]]).casefold()
    terms = {term for term in query.casefold().split() if term}
    if not terms:
        return 0.0
    matches = sum(1 for term in terms if term in haystack)
    return matches / len(terms)


__all__ = ["HybridRetriever", "HybridSearchResult", "RagDocument", "load_rag_documents"]
