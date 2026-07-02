"""RAG ingestion pipeline tests (Task 136)."""

from __future__ import annotations

import json

from proseforge_agent.retrieval.ingestion import RagIngestionPipeline
from proseforge_agent.cli import main


def test_rag_ingestion_writes_chunks_and_skips_unchanged_checksums(tmp_path):
    workspace = tmp_path / "workspace"
    chapter = workspace / "demo_novel" / "chapters" / "ch_001.md"
    bible = workspace / "demo_novel" / "bible" / "characters.yaml"
    chapter.parent.mkdir(parents=True)
    bible.parent.mkdir(parents=True)
    chapter.write_text("hero memory", encoding="utf-8")
    bible.write_text("hero: brave", encoding="utf-8")
    pipeline = RagIngestionPipeline(workspace)

    first = pipeline.ingest_project("demo_novel")
    second = pipeline.ingest_project("demo_novel")

    assert first.added_count == 2
    assert second.unchanged_count == 2
    chunks = [json.loads(line) for line in (workspace / "demo_novel" / "rag" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {chunk["source_type"] for chunk in chunks} == {"chapter", "bible"}
    assert {chunk["embedding_status"] for chunk in chunks} == {"embedded"}
    assert all(chunk["checksum"] for chunk in chunks)


def test_rag_ingestion_file_adds_imported_file_chunk(tmp_path):
    workspace = tmp_path / "workspace"
    research = tmp_path / "research.md"
    research.write_text("research note", encoding="utf-8")

    result = RagIngestionPipeline(workspace).ingest_file(research, slug="demo_novel")

    assert result.added_count == 1
    chunks = [json.loads(line) for line in (workspace / "demo_novel" / "rag" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert chunks[0]["source_type"] == "imported_file"


def test_rag_ingestion_splits_long_chapter_into_multiple_chunks(tmp_path):
    workspace = tmp_path / "workspace"
    chapter = workspace / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("\n\n".join(f"paragraph {index} " * 30 for index in range(20)), encoding="utf-8")

    result = RagIngestionPipeline(workspace).ingest_project("demo_novel")

    chunks = [
        json.loads(line)
        for line in (workspace / "demo_novel" / "rag" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert result.added_count > 1
    assert len(chunks) > 1
    assert {chunk["metadata"]["chunk_index"] for chunk in chunks} == set(range(len(chunks)))
    assert all(chunk["id"].endswith(f":{chunk['metadata']['chunk_index']}") for chunk in chunks)


def test_rag_ingestion_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    chapter = tmp_path / ".pf-agent" / "workspace" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("hero memory", encoding="utf-8")
    research = tmp_path / "research.md"
    research.write_text("research note", encoding="utf-8")

    assert main(["rag", "ingest", "--slug", "demo_novel"]) == 0
    assert main(["rag", "ingest-file", str(research), "--slug", "demo_novel"]) == 0
    assert main(["rag", "status", "--slug", "demo_novel"]) == 0

    out = capsys.readouterr().out
    assert "RAG Ingestion" in out
    assert "RAG Status" in out
