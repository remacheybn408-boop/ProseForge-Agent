"""Evidence pack retrieval tests (Task 137)."""

from __future__ import annotations

from proseforge_agent.memory.store import MemoryItem, MemoryStore
from proseforge_agent.retrieval.evidence import EvidencePackBuilder
from proseforge_agent.retrieval.hybrid import HybridSearchResult


class _FakeRagSearcher:
    def __init__(self, results: list[HybridSearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, str]] = []

    def search(self, query: str, *, project_slug: str, top_k: int = 5):
        self.calls.append((query, project_slug))
        return self.results[:top_k]


def test_evidence_pack_includes_rag_chunks_with_source_scores():
    store = MemoryStore(":memory:")
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="hard canon", source="memory:1"))
    rag = _FakeRagSearcher(
        [
            HybridSearchResult(
                id="chunk-1",
                text="old chapter scene",
                project_slug="demo",
                metadata={"source": "ch_001"},
                score=0.9,
                keyword_score=0.4,
                vector_score=0.5,
                channels=["keyword", "vector"],
            )
        ]
    )

    pack = EvidencePackBuilder(store, rag_searcher=rag).build("demo", "chapter_draft", token_budget=1000)

    sources = [item.source for item in pack.items]
    assert "memory:1" in sources
    assert "ch_001" in sources
    rag_item = next(item for item in pack.items if item.source == "ch_001")
    assert rag_item.type == "rag_chunk"
    assert rag_item.score == 0.9
    assert rag.calls[0][1] == "demo"


def test_evidence_pack_deduplicates_rag_sources_against_memory():
    store = MemoryStore(":memory:")
    store.add(MemoryItem(project_slug="demo", type="canon_fact", text="hard canon", source="ch_001"))
    rag = _FakeRagSearcher(
        [
            HybridSearchResult(
                id="chunk-1",
                text="duplicate chapter scene",
                project_slug="demo",
                metadata={"source": "ch_001"},
                score=0.9,
                keyword_score=0.4,
                vector_score=0.5,
                channels=["keyword", "vector"],
            )
        ]
    )

    pack = EvidencePackBuilder(store, rag_searcher=rag).build("demo", "chapter_draft", token_budget=1000)

    assert [item.source for item in pack.items].count("ch_001") == 1
