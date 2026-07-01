"""Automatic retrieval and evidence packs.

Workflows request context by intent and receive ranked, sectioned, cited
evidence packs. This package reads the memory store and the engine adapter's
read helpers; it does not import workflow or provider implementations.
"""

from .evidence import EvidencePack, EvidencePackBuilder
from .embeddings import EmbeddingConfig, EmbeddingProvider, FakeEmbeddingProvider, build_embedding_provider
from .hybrid import HybridRetriever, HybridSearchResult, RagDocument, load_rag_documents
from .index import MemoryIndex, ScoredItem
from .router import EvidenceItem, RetrievalRequest, RetrievalRouter
from .vector_store import JsonlVectorStore, SqliteVectorStore, VectorSearchResult, VectorStore, build_vector_store

__all__ = [
    "EvidencePack",
    "EvidencePackBuilder",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "HybridRetriever",
    "HybridSearchResult",
    "MemoryIndex",
    "RagDocument",
    "ScoredItem",
    "EvidenceItem",
    "RetrievalRequest",
    "RetrievalRouter",
    "JsonlVectorStore",
    "SqliteVectorStore",
    "VectorSearchResult",
    "VectorStore",
    "build_embedding_provider",
    "build_vector_store",
    "load_rag_documents",
]
