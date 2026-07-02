"""MemoryStore cross-thread + IdempotencyStore atomicity (Task 201)."""

from __future__ import annotations

import threading

from proseforge_agent.cron.core import IdempotencyStore
from proseforge_agent.memory import MemoryItem, MemoryStore


def test_memory_store_add_from_second_thread(tmp_path):
    store = MemoryStore(tmp_path / "mem.sqlite")
    errors: list[Exception] = []

    def worker():
        try:
            store.add(MemoryItem(project_slug="demo", type="canon_fact", text="X", source="thread"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    assert errors == []  # no sqlite ProgrammingError across threads


def test_memory_store_concurrent_adds_all_persist(tmp_path):
    store = MemoryStore(tmp_path / "mem.sqlite")

    def worker(n):
        store.add(MemoryItem(project_slug="demo", type="canon_fact", text=f"t{n}", source="s"))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store.list(project_slug="demo")) == 8


def test_idempotency_concurrent_remember_loses_no_nonce(tmp_path):
    store = IdempotencyStore(tmp_path)

    def worker(n):
        store.remember(f"nonce-{n}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for i in range(20):
        assert store.seen(f"nonce-{i}"), f"lost nonce-{i}"


def test_idempotency_write_leaves_valid_json_and_no_tmp(tmp_path):
    store = IdempotencyStore(tmp_path)
    store.remember("a")
    store.remember("b")

    import json

    payload = json.loads(store.path.read_text(encoding="utf-8"))
    assert set(payload["nonces"]) == {"a", "b"}
    # no leftover temp file
    assert not any(p.name.endswith(".tmp") for p in tmp_path.iterdir())


def test_idempotency_corrupt_json_treated_as_empty(tmp_path):
    store = IdempotencyStore(tmp_path)
    store.path.write_text("{ this is not valid json", encoding="utf-8")

    assert store.seen("anything") is False  # does not raise
    store.remember("fresh")  # recovers
    assert store.seen("fresh") is True


def test_idempotency_still_detects_duplicate_nonce(tmp_path):
    store = IdempotencyStore(tmp_path)
    store.remember("dup")
    assert store.seen("dup") is True
