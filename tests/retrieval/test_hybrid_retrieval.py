"""Hybrid retrieval tests (Task 135)."""

from __future__ import annotations

import json

from proseforge_agent.retrieval.embeddings import FakeEmbeddingProvider
from proseforge_agent.retrieval.hybrid import HybridRetriever, RagDocument
from proseforge_agent.retrieval.vector_store import JsonlVectorStore
from proseforge_agent.cli import main


def test_hybrid_retrieval_combines_keyword_vector_and_project_scope(tmp_path):
    documents = [
        RagDocument(id="demo-hero", text="hero memory", project_slug="demo", metadata={"source": "ch_001"}),
        RagDocument(id="other-hero", text="hero memory", project_slug="other", metadata={"source": "ch_999"}),
    ]
    retriever = HybridRetriever(
        documents,
        embedding_provider=FakeEmbeddingProvider(dimension=8),
        vector_store=JsonlVectorStore(tmp_path / "vectors.jsonl"),
    )

    results = retriever.search("hero memory", project_slug="demo", top_k=5)

    assert [result.id for result in results] == ["demo-hero"]
    assert results[0].keyword_score > 0
    assert results[0].vector_score > 0
    assert "keyword" in results[0].channels
    assert "vector" in results[0].channels
    assert results[0].metadata["source"] == "ch_001"


def test_hybrid_retrieval_cli_search(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    chunks_dir = tmp_path / ".pf-agent" / "workspace" / "demo_novel" / "rag"
    chunks_dir.mkdir(parents=True)
    (chunks_dir / "chunks.jsonl").write_text(
        json.dumps(
            {
                "id": "chunk-1",
                "text": "hero memory",
                "project_slug": "demo_novel",
                "metadata": {"source": "ch_001"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    assert main(["rag", "search", "hero memory", "--slug", "demo_novel"]) == 0

    out = capsys.readouterr().out
    assert "Hybrid RAG Search" in out
    assert "chunk-1" in out


def test_rag_document_loader_accepts_utf8_bom_jsonl(tmp_path):
    from proseforge_agent.retrieval.hybrid import load_rag_documents

    path = tmp_path / "chunks.jsonl"
    payload = '{"id":"chunk-1","text":"hero memory","project_slug":"demo","metadata":{}}\n'
    path.write_bytes(b"\xef\xbb\xbf" + payload.encode("utf-8"))

    assert load_rag_documents(path)[0].id == "chunk-1"
