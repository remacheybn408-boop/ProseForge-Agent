"""Automatic retrieval and evidence packs.

Workflows request context by intent and receive ranked, sectioned, cited
evidence packs. This package reads the memory store and the engine adapter's
read helpers; it does not import workflow or provider implementations.
"""

from .evidence import EvidencePack, EvidencePackBuilder
from .embeddings import EmbeddingConfig, EmbeddingProvider, FakeEmbeddingProvider, build_embedding_provider
from .evaluation import RagEvalCase, RagEvalResult, RagEvaluator, default_eval_cases_from_documents, load_eval_cases
from .hybrid import HybridRetriever, HybridSearchResult, RagDocument, load_rag_documents
from .ingestion import RagIngestionPipeline, RagIngestionReport
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
    "RagEvalCase",
    "RagEvalResult",
    "RagEvaluator",
    "RagIngestionPipeline",
    "RagIngestionReport",
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
    "default_eval_cases_from_documents",
    "load_eval_cases",
    "load_rag_documents",
]
