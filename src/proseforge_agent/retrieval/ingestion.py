"""RAG ingestion pipeline for project files and imported research."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .embeddings import EmbeddingProvider, FakeEmbeddingProvider
from .vector_store import JsonlVectorStore, VectorStore

_SUPPORTED_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json"}


@dataclass(frozen=True)
class RagIngestionReport:
    """Summary of a RAG ingestion run."""

    slug: str
    added_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    total_chunks: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class RagIngestionPipeline:
    """Chunk project content and maintain a local vector index."""

    def __init__(
        self,
        workspace: str | Path,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.embedding_provider = embedding_provider or FakeEmbeddingProvider()
        self._vector_store = vector_store

    def ingest_project(self, slug: str) -> RagIngestionReport:
        project_dir = self.workspace / slug
        chunks = [
            self._chunk_for_file(path, slug=slug, project_dir=project_dir)
            for path in sorted(project_dir.rglob("*"))
            if path.is_file() and path.suffix.lower() in _SUPPORTED_SUFFIXES and "rag" not in path.relative_to(project_dir).parts
        ]
        return self._write_chunks(slug, chunks)

    def ingest_file(self, path: str | Path, *, slug: str) -> RagIngestionReport:
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8-sig")
        chunk = self._chunk(
            slug=slug,
            source=str(file_path),
            source_type="imported_file",
            text=text,
            metadata={"source": str(file_path), "source_type": "imported_file"},
        )
        return self._write_chunks(slug, [chunk])

    def status(self, slug: str) -> RagIngestionReport:
        chunks = self._read_chunks(slug)
        return RagIngestionReport(slug=slug, total_chunks=len(chunks))

    def _chunk_for_file(self, path: Path, *, slug: str, project_dir: Path) -> dict:
        relative = path.relative_to(project_dir).as_posix()
        source_type = _source_type(path.relative_to(project_dir).parts)
        return self._chunk(
            slug=slug,
            source=relative,
            source_type=source_type,
            text=path.read_text(encoding="utf-8-sig"),
            metadata={"source": relative, "source_type": source_type},
        )

    def _chunk(self, *, slug: str, source: str, source_type: str, text: str, metadata: dict) -> dict:
        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunk_id = hashlib.sha1(f"{slug}:{source}:0".encode("utf-8")).hexdigest()[:16]
        return {
            "id": chunk_id,
            "source_type": source_type,
            "project_slug": slug,
            "chapter_id": _chapter_id(source),
            "scene_id": _scene_id(source),
            "text": text,
            "checksum": checksum,
            "embedding_status": "embedded",
            "metadata": {**metadata, "checksum": checksum, "project_slug": slug},
        }

    def _write_chunks(self, slug: str, incoming: list[dict]) -> RagIngestionReport:
        existing = {chunk["id"]: chunk for chunk in self._read_chunks(slug)}
        added = updated = unchanged = 0
        for chunk in incoming:
            previous = existing.get(chunk["id"])
            if previous is None:
                added += 1
            elif previous.get("checksum") == chunk["checksum"]:
                unchanged += 1
                continue
            else:
                updated += 1
            existing[chunk["id"]] = chunk
            self._vector_store_for(slug).upsert(chunk["id"], self.embedding_provider.embed_text(chunk["text"]), chunk["metadata"])
        chunks = sorted(existing.values(), key=lambda item: item["id"])
        chunks_path = self._chunks_path(slug)
        chunks_path.parent.mkdir(parents=True, exist_ok=True)
        chunks_path.write_text(
            "".join(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n" for chunk in chunks),
            encoding="utf-8",
        )
        return RagIngestionReport(
            slug=slug,
            added_count=added,
            updated_count=updated,
            unchanged_count=unchanged,
            total_chunks=len(chunks),
        )

    def _read_chunks(self, slug: str) -> list[dict]:
        path = self._chunks_path(slug)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    def _chunks_path(self, slug: str) -> Path:
        return self.workspace / slug / "rag" / "chunks.jsonl"

    def _vector_store_for(self, slug: str) -> VectorStore:
        if self._vector_store is not None:
            return self._vector_store
        return JsonlVectorStore(self.workspace / slug / "rag" / "vectors.jsonl")


def _source_type(parts: tuple[str, ...]) -> str:
    if not parts:
        return "project"
    head = parts[0].lower()
    return {
        "chapters": "chapter",
        "scenes": "scene",
        "bible": "bible",
        "timeline": "timeline",
        "rules": "rules",
        "imports": "imported_file",
        "imported": "imported_file",
        "sessions": "session_summary",
    }.get(head, "project")


def _chapter_id(source: str) -> str:
    path = Path(source)
    return path.stem if "chapter" in source.lower() or "chapters" in source.lower() else ""


def _scene_id(source: str) -> str:
    path = Path(source)
    return path.stem if "scene" in source.lower() or "scenes" in source.lower() else ""


__all__ = ["RagIngestionPipeline", "RagIngestionReport"]
