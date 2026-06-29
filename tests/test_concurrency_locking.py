"""Tests for cross-platform concurrency and locking (Task 65)."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from proseforge_agent.concurrency import FileLock, LockError, with_sqlite_retry
from proseforge_agent.errors import ProseForgeAgentError

FIXTURE = (
    Path(__file__).parent / "fixtures" / "concurrency-and-locking" / "state_seed.json"
)


@dataclass
class WriterResults:
    both_committed: bool
    final_count: int


def run_two_concurrent_writers(target: Path, lock_factory) -> WriterResults:
    """Two threads each increment a shared JSON counter under the lock."""
    seed = json.loads(FIXTURE.read_text(encoding="utf-8"))
    target.write_text(json.dumps(seed), encoding="utf-8")
    lock_path = target.with_suffix(".lock")
    committed: list[str] = []

    def writer(name: str) -> None:
        with lock_factory(lock_path, timeout=5.0):
            data = json.loads(target.read_text(encoding="utf-8"))
            data["count"] += 1
            data["writers"].append(name)
            time.sleep(0.02)  # widen the race window
            target.write_text(json.dumps(data), encoding="utf-8")
            committed.append(name)

    threads = [threading.Thread(target=writer, args=(f"w{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final = json.loads(target.read_text(encoding="utf-8"))
    return WriterResults(both_committed=len(committed) == 2, final_count=final["count"])


def test_two_writers_serialize_without_losing_writes(tmp_path):
    target = tmp_path / "state.json"
    results = run_two_concurrent_writers(target, FileLock)
    assert results.both_committed is True
    assert results.final_count == 2  # neither write was lost


def test_lock_timeout_raises_clean_error_without_corruption(tmp_path):
    target = tmp_path / "state.json"
    target.write_text(json.dumps({"count": 0}), encoding="utf-8")
    lock_path = tmp_path / "state.lock"
    holder = FileLock(lock_path, timeout=5.0)
    holder.acquire()
    try:
        contender = FileLock(lock_path, timeout=0.2)
        with pytest.raises(ProseForgeAgentError):
            contender.acquire()
        # Data is untouched by the failed acquisition.
        assert json.loads(target.read_text(encoding="utf-8")) == {"count": 0}
    finally:
        holder.release()


def test_sqlite_busy_is_retried_within_bound():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise sqlite3.OperationalError("database is locked")
        return "ok"

    assert with_sqlite_retry(flaky, busy_timeout=2.0, poll_interval=0.01) == "ok"
    assert calls["n"] == 3

    def always_locked():
        raise sqlite3.OperationalError("database is locked")

    with pytest.raises(sqlite3.OperationalError):
        with_sqlite_retry(always_locked, busy_timeout=0.1, poll_interval=0.01)


def test_lock_released_on_exception_in_context_manager(tmp_path):
    lock_path = tmp_path / "x.lock"
    with pytest.raises(ValueError):
        with FileLock(lock_path, timeout=2.0):
            raise ValueError("boom")
    # The lock is free again: a fresh acquisition succeeds immediately.
    second = FileLock(lock_path, timeout=0.5)
    second.acquire()
    second.release()


def test_stale_lock_file_is_recoverable(tmp_path):
    lock_path = tmp_path / "stale.lock"
    # A lock file left on disk by a dead process is not itself locked.
    lock_path.write_text("", encoding="utf-8")
    lock = FileLock(lock_path, timeout=0.5)
    lock.acquire()
    lock.release()


def test_lock_path_handles_utf8_and_spaces(tmp_path):
    lock_path = tmp_path / "状态 文件.lock"
    lock = FileLock(lock_path, timeout=1.0)
    with lock:
        assert lock_path.exists()
