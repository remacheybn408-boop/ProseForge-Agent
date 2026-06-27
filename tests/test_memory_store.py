import json
from pathlib import Path

import pytest

from proseforge_agent.errors import MemoryError
from proseforge_agent.memory import MemoryItem, MemoryStore

FIXTURE = Path(__file__).parent / "fixtures" / "memory" / "items.jsonl"


def test_memory_item_can_be_added_and_superseded(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    first = store.add(
        MemoryItem(project_slug="demo", type="canon_fact", text="Hero fears water", source="manual")
    )
    second = store.supersede(first.id, text="Hero fears deep water")
    assert store.get(first.id).status == "superseded"
    assert store.get(second.id).supersedes == first.id


def test_add_assigns_id_and_timestamps(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    item = store.add(
        MemoryItem(project_slug="demo", type="canon_fact", text="X", source="manual")
    )
    assert item.id is not None
    assert item.created_at
    assert item.updated_at
    assert item.status == "active"


def test_get_returns_none_for_missing_id(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    assert store.get(999) is None


def test_list_filters_by_project_and_status(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    a = store.add(MemoryItem(project_slug="demo", type="fact", text="a", source="m"))
    store.add(MemoryItem(project_slug="other", type="fact", text="b", source="m"))
    store.supersede(a.id, text="a2")
    demo_active = store.list(project_slug="demo", status="active")
    assert {item.text for item in demo_active} == {"a2"}
    assert {item.project_slug for item in store.list(project_slug="demo")} == {"demo"}


def test_add_with_empty_source_fails_validation(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    with pytest.raises(MemoryError):
        store.add(MemoryItem(project_slug="demo", type="fact", text="x", source=""))


def test_supersede_missing_item_fails(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    with pytest.raises(MemoryError):
        store.supersede(123, text="new")


def test_tags_roundtrip(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    item = store.add(
        MemoryItem(
            project_slug="demo",
            type="fact",
            text="x",
            source="m",
            tags=["血玉", "limit"],
        )
    )
    assert store.get(item.id).tags == ["血玉", "limit"]


def test_export_includes_active_and_superseded(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    first = store.add(MemoryItem(project_slug="demo", type="fact", text="a", source="m"))
    store.supersede(first.id, text="a2")
    exported = store.export(project_slug="demo")
    statuses = {row["status"] for row in exported}
    assert statuses == {"active", "superseded"}
    assert len(exported) == 2


def test_writes_persist_across_reopen(tmp_path):
    db = tmp_path / "memory.sqlite"
    first = MemoryStore(db).add(
        MemoryItem(project_slug="demo", type="fact", text="durable", source="m")
    )
    reopened = MemoryStore(db)
    assert reopened.get(first.id).text == "durable"


def test_items_fixture_loads(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    lines = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for row in lines:
        store.add(MemoryItem(**row))
    assert len(store.list()) == len(lines)
