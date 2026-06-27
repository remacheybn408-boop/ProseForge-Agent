import sqlite3

from proseforge_agent.memory.schema import SCHEMA_VERSION, apply_schema


def test_apply_schema_creates_memory_items_table(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.sqlite")
    apply_schema(conn)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='memory_items'"
    ).fetchall()
    assert rows


def test_apply_schema_is_idempotent(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.sqlite")
    apply_schema(conn)
    apply_schema(conn)  # must not raise
    version = conn.execute(
        "SELECT value FROM schema_meta WHERE key='version'"
    ).fetchone()
    assert int(version[0]) == SCHEMA_VERSION


def test_memory_items_table_has_expected_columns(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.sqlite")
    apply_schema(conn)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(memory_items)")}
    expected = {
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
    }
    assert expected <= cols
