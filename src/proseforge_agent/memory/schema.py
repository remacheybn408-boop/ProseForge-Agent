"""Agent memory database schema.

The Agent keeps its long-form novel memory in its own SQLite database, separate
from the ProseForge engine's ``novel.db``. This module owns the table
definitions and a single idempotent ``apply_schema`` entry point. Full-text
search, memory links, and retrieval logs are added by later memory/retrieval
tasks; this card establishes the auditable ``memory_items`` table.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

MEMORY_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS memory_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT    NOT NULL,
    type         TEXT    NOT NULL,
    text         TEXT    NOT NULL,
    source       TEXT    NOT NULL,
    confidence   REAL    NOT NULL DEFAULT 1.0,
    tags_json    TEXT    NOT NULL DEFAULT '[]',
    status       TEXT    NOT NULL DEFAULT 'active',
    supersedes   INTEGER,
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL
)
"""

MEMORY_ITEMS_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_memory_items_project_status
    ON memory_items (project_slug, status)
"""

SCHEMA_META_DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create the memory schema if absent and record the schema version."""
    with conn:
        conn.execute(MEMORY_ITEMS_DDL)
        conn.execute(MEMORY_ITEMS_INDEX_DDL)
        conn.execute(SCHEMA_META_DDL)
        conn.execute(
            "INSERT INTO schema_meta (key, value) VALUES ('version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(SCHEMA_VERSION),),
        )


__all__ = [
    "SCHEMA_VERSION",
    "MEMORY_ITEMS_DDL",
    "apply_schema",
]
