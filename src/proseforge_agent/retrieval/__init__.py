"""Automatic retrieval and evidence packs.

Workflows request context by intent and receive ranked, sectioned, cited
evidence packs. This package reads the memory store and the engine adapter's
read helpers; it does not import workflow or provider implementations.
"""

from .evidence import EvidencePack, EvidencePackBuilder
from .embeddings import EmbeddingConfig, EmbeddingProvider, FakeEmbeddingProvider, build_embedding_provider
from .index import MemoryIndex, ScoredItem
from .router import EvidenceItem, RetrievalRequest, RetrievalRouter

__all__ = [
    "EvidencePack",
    "EvidencePackBuilder",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "FakeEmbeddingProvider",
    "MemoryIndex",
    "ScoredItem",
    "EvidenceItem",
    "RetrievalRequest",
    "RetrievalRouter",
    "build_embedding_provider",
]
