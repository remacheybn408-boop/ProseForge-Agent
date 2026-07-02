"""Vector store adapters for local RAG retrieval."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..concurrency import FileLock, with_sqlite_retry
from ..errors import ConfigurationError


@dataclass(frozen=True)
class VectorSearchResult:
    """One vector search hit."""

    id: str
    score: float
    metadata: dict

    def to_dict(self) -> dict:
        return {"id": self.id, "score": self.score, "metadata": dict(self.metadata)}


class VectorStore(Protocol):
    """Minimal vector store contract."""

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        """Insert or replace a vector."""

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        """Return top-k nearest vectors."""

    def delete(self, id: str) -> None:
        """Delete a vector by id."""


class JsonlVectorStore:
    """Small local JSONL vector store for offline retrieval."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        with FileLock(self.path.with_suffix(self.path.suffix + ".lock")):
            records = [record for record in self._read_records() if record["id"] != id]
            records.append({"id": id, "vector": list(vector), "metadata": dict(metadata)})
            self._write_records(records)

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        results = [
            VectorSearchResult(
                id=str(record["id"]),
                score=_cosine_similarity(vector, list(record["vector"])),
                metadata=dict(record.get("metadata") or {}),
            )
            for record in self._read_records()
        ]
        results.sort(key=lambda item: (-item.score, item.id))
        return results[: max(0, top_k)]

    def delete(self, id: str) -> None:
        with FileLock(self.path.with_suffix(self.path.suffix + ".lock")):
            self._write_records([record for record in self._read_records() if record["id"] != id])

    def _read_records(self) -> list[dict]:
        if not self.path.exists():
            return []
        records: list[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and "id" in payload and "vector" in payload:
                records.append(payload)
        return records

    def _write_records(self, records: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
        self.path.write_text(payload, encoding="utf-8")


class InMemoryVectorStore:
    """Process-local vector store used when callers do not request persistence."""

    def __init__(self) -> None:
        self._records: dict[str, dict] = {}

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        self._records[id] = {"id": id, "vector": list(vector), "metadata": dict(metadata)}

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        results = [
            VectorSearchResult(
                id=str(record["id"]),
                score=_cosine_similarity(vector, list(record["vector"])),
                metadata=dict(record.get("metadata") or {}),
            )
            for record in self._records.values()
        ]
        results.sort(key=lambda item: (-item.score, item.id))
        return results[: max(0, top_k)]

    def delete(self, id: str) -> None:
        self._records.pop(id, None)


class SqliteVectorStore:
    """SQLite-backed local vector store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        with self._lock:
            self._conn.execute("PRAGMA busy_timeout = 5000")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS vectors (id TEXT PRIMARY KEY, vector_json TEXT NOT NULL, metadata_json TEXT NOT NULL)"
            )

    def upsert(self, id: str, vector: list[float], metadata: dict) -> None:
        def operation() -> None:
            with self._lock:
                with self._conn:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO vectors (id, vector_json, metadata_json) VALUES (?, ?, ?)",
                        (id, json.dumps(list(vector)), json.dumps(dict(metadata), ensure_ascii=False, sort_keys=True)),
                    )

        with_sqlite_retry(operation)

    def search(self, vector: list[float], top_k: int) -> list[VectorSearchResult]:
        def operation() -> list[tuple]:
            with self._lock:
                return self._conn.execute("SELECT id, vector_json, metadata_json FROM vectors").fetchall()

        rows = with_sqlite_retry(operation)
        results = [
            VectorSearchResult(
                id=str(row[0]),
                score=_cosine_similarity(vector, json.loads(row[1])),
                metadata=json.loads(row[2]),
            )
            for row in rows
        ]
        results.sort(key=lambda item: (-item.score, item.id))
        return results[: max(0, top_k)]

    def delete(self, id: str) -> None:
        def operation() -> None:
            with self._lock:
                with self._conn:
                    self._conn.execute("DELETE FROM vectors WHERE id = ?", (id,))

        with_sqlite_retry(operation)


def build_vector_store(config: dict | None = None) -> VectorStore:
    """Build a vector store adapter."""
    config = dict(config or {})
    provider = str(config.get("provider", "jsonl")).lower().replace("-", "_")
    path = config.get("path", "vectors.jsonl")
    if provider == "jsonl":
        return JsonlVectorStore(path)
    if provider == "sqlite":
        return SqliteVectorStore(path)
    if provider in {"chroma", "qdrant", "faiss"}:
        raise ConfigurationError(f"{provider} vector store is not configured")
    raise ConfigurationError(f"unknown vector store provider: {provider}")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ConfigurationError("vector dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


__all__ = [
    "JsonlVectorStore",
    "InMemoryVectorStore",
    "SqliteVectorStore",
    "VectorSearchResult",
    "VectorStore",
    "build_vector_store",
]
