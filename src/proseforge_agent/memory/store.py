"""Durable, auditable store for long-form novel memory.

Memory is project state, not prompt scratch text: accepted and superseded
facts are never hard-deleted, so the history stays auditable. Writes are
transaction protected, and every item must carry a source reference.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..concurrency import FileLock
from ..errors import MemoryError
from .schema import apply_schema

_COLUMNS = (
    "id",
    "project_slug",
    "type",
    "text",
    "source",
    "confidence",
    "tags_json",
    "status",
    "supersedes",
    "created_at",
    "updated_at",
)


@dataclass
class MemoryItem:
    """One auditable memory fact."""

    project_slug: str
    type: str
    text: str
    source: str
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)
    status: str = "active"
    supersedes: int | None = None
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """SQLite-backed memory store."""

    def __init__(self, db_path: str | Path) -> None:
        # check_same_thread=False lets background jobs, the chat REPL, and the
        # local API share this store; writers are serialized by the FileLock
        # below plus busy_timeout (finding 2.1).
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        # Wait out transient contention at the SQLite layer; serialize file-level
        # writers with an advisory lock alongside the db file.
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._lock = None if str(db_path) == ":memory:" else FileLock(str(db_path) + ".lock")
        # In-process serialization: the shared connection and the per-instance
        # FileLock (which is reentrant per instance) do not serialize threads on
        # their own, so guard writes with a thread lock too (finding 2.1).
        self._thread_lock = threading.RLock()
        self.initialize()

    @contextmanager
    def _write_lock(self):
        with self._thread_lock:
            if self._lock is not None:
                with self._lock:
                    yield
            else:
                yield

    def initialize(self) -> None:
        apply_schema(self._conn)

    def close(self) -> None:
        """Close the underlying SQLite connection (releases the file lock)."""
        self._conn.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- writes ----------------------------------------------------------

    def add(self, item: MemoryItem) -> MemoryItem:
        self._validate(item)
        now = _now()
        with self._write_lock(), self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO memory_items
                    (project_slug, type, text, source, confidence, tags_json,
                     status, supersedes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.project_slug,
                    item.type,
                    item.text,
                    item.source,
                    item.confidence,
                    json.dumps(item.tags, ensure_ascii=False),
                    item.status or "active",
                    item.supersedes,
                    now,
                    now,
                ),
            )
            new_id = cursor.lastrowid
        return self.get(new_id)

    def supersede(self, old_id: int, *, text: str, **overrides) -> MemoryItem:
        old = self.get(old_id)
        if old is None:
            raise MemoryError(f"cannot supersede unknown memory item {old_id}")
        now = _now()
        new_item = MemoryItem(
            project_slug=overrides.get("project_slug", old.project_slug),
            type=overrides.get("type", old.type),
            text=text,
            source=overrides.get("source", old.source),
            confidence=overrides.get("confidence", old.confidence),
            tags=overrides.get("tags", list(old.tags)),
            status="active",
            supersedes=old_id,
        )
        self._validate(new_item)
        with self._write_lock(), self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO memory_items
                    (project_slug, type, text, source, confidence, tags_json,
                     status, supersedes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_item.project_slug,
                    new_item.type,
                    new_item.text,
                    new_item.source,
                    new_item.confidence,
                    json.dumps(new_item.tags, ensure_ascii=False),
                    new_item.status,
                    old_id,
                    now,
                    now,
                ),
            )
            new_id = cursor.lastrowid
            self._conn.execute(
                "UPDATE memory_items SET status = 'superseded', updated_at = ? WHERE id = ?",
                (now, old_id),
            )
        return self.get(new_id)

    def mark_superseded(self, item_id: int) -> None:
        """Mark a single item superseded. Used by many-to-one compaction."""
        if self.get(item_id) is None:
            raise MemoryError(f"cannot supersede unknown memory item {item_id}")
        with self._write_lock(), self._conn:
            self._conn.execute(
                "UPDATE memory_items SET status = 'superseded', updated_at = ? WHERE id = ?",
                (_now(), item_id),
            )

    # -- reads -----------------------------------------------------------

    def get(self, item_id: int) -> MemoryItem | None:
        row = self._conn.execute(
            "SELECT * FROM memory_items WHERE id = ?", (item_id,)
        ).fetchone()
        return self._row_to_item(row) if row else None

    def list(
        self, project_slug: str | None = None, status: str | None = None
    ) -> list[MemoryItem]:
        clauses = []
        params: list = []
        if project_slug is not None:
            clauses.append("project_slug = ?")
            params.append(project_slug)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM memory_items {where} ORDER BY id ASC", params
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def export(self, project_slug: str | None = None) -> list[dict]:
        items = self.list(project_slug=project_slug)
        return [
            {
                "id": item.id,
                "project_slug": item.project_slug,
                "type": item.type,
                "text": item.text,
                "source": item.source,
                "confidence": item.confidence,
                "tags": item.tags,
                "status": item.status,
                "supersedes": item.supersedes,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in items
        ]

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _validate(item: MemoryItem) -> None:
        for field_name in ("project_slug", "type", "text", "source"):
            if not getattr(item, field_name):
                raise MemoryError(
                    f"memory item is missing required field {field_name!r}"
                )

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            project_slug=row["project_slug"],
            type=row["type"],
            text=row["text"],
            source=row["source"],
            confidence=row["confidence"],
            tags=json.loads(row["tags_json"]),
            status=row["status"],
            supersedes=row["supersedes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


__all__ = ["MemoryItem", "MemoryStore"]
