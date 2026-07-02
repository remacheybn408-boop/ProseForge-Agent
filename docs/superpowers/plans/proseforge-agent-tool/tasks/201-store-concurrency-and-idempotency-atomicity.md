# Task 201: MemoryStore Cross-Thread + IdempotencyStore Atomicity / 存储并发与幂等原子性

## Goal

Two data-integrity fixes:

1. **`MemoryStore` cross-thread crash** — the store opens SQLite with the
   default `check_same_thread=True` and holds one connection created at
   construction. The `concurrency.py` docstring promises chat + background jobs
   + local API share the DB, but any second-thread `.add()/.list()/.get()`
   raises `sqlite3.ProgrammingError`.
2. **`IdempotencyStore` lost-update race + non-atomic write** —
   `remember(nonce)` (`cron/core.py:75`) does read-JSON → mutate →
   `write_text` with no lock and no atomic rename. Concurrent fires lose
   nonces; a crash mid-write leaves truncated JSON that poisons every later
   `verify()` with an unhandled `json.JSONDecodeError`.

## Architecture Notes

Fixes **findings 2.1 and 2.2** (High · Correctness) of
`docs/review/core-review-2026-07-01.md`. Both reuse `concurrency.FileLock`
(already in the repo) rather than inventing new machinery.

Design — MemoryStore (`memory/store.py`):

- Open with `sqlite3.connect(str(db_path), check_same_thread=False)`.
- Serialize writes with the existing `concurrency.FileLock` and set
  `PRAGMA busy_timeout` (reuse `with_sqlite_retry` if already present).
- Add a regression test that spawns a thread and calls `.add()`.

Design — IdempotencyStore (`cron/core.py`):

- Wrap the read-modify-write of `remember` in `concurrency.FileLock`.
- Write to `path.with_suffix(".json.tmp")` then `os.replace(tmp, path)` for
  atomic commit.
- In `_load()`, catch `json.JSONDecodeError` and treat it as "no nonces yet"
  (return empty), emitting a WARNING event so the corruption is visible.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (findings 2.1, 2.2; notes 2.3, 2.4)
- `src/proseforge_agent/concurrency.py` (`FileLock`, `with_sqlite_retry`)
- 07-memory-schema-and-store.md, 180-hosted-cron-and-scale-to-zero.md
- `src/proseforge_agent/memory/store.py`, `cron/core.py`

## Files

- Modify `src/proseforge_agent/memory/store.py` (connection flag + locked
  writes).
- Modify `src/proseforge_agent/cron/core.py` (`remember` lock + atomic write;
  `_load` JSONDecodeError handling + WARNING).
- Add tests in `tests/test_store_concurrency_and_idempotency.py`.

## Interfaces / Contracts

- `MemoryStore` methods are safe to call from a second thread (no
  `ProgrammingError`); writes serialize via `FileLock`.
- `IdempotencyStore.remember` under concurrency never loses a nonce; the store
  file is always valid JSON (atomic replace).
- A truncated/corrupt nonce file is treated as empty with a WARNING, not an
  unhandled crash.

## Data Flow

1. Job runner thread calls `store.add(candidate)` while the REPL thread holds
   the store → no crash (shared connection + lock).
2. Two cron fires call `remember(n1)` / `remember(n2)` concurrently → both
   persisted (lock serializes read-modify-write, atomic replace commits).

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_store_concurrency_and_idempotency.py::test_memory_store_add_from_second_thread`**

```python
def test_memory_store_add_from_second_thread(tmp_path):
    store = MemoryStore(tmp_path / "mem.db")
    errors = []

    def worker():
        try:
            store.add(sample_memory())
        except Exception as exc:   # noqa: BLE001
            errors.append(exc)

    t = threading.Thread(target=worker)
    t.start(); t.join()

    assert errors == []            # no sqlite ProgrammingError
```

- [ ] **Step 2: Run the targeted test and confirm failure** (raises
  `sqlite3.ProgrammingError: SQLite objects created in a thread…`).

- [ ] **Step 3: Set `check_same_thread=False` + lock writes; add
  `IdempotencyStore` lock + atomic write + corrupt-file handling.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_memory_store_writes_serialize_under_filelock
test_idempotency_concurrent_remember_loses_no_nonce
test_idempotency_write_is_atomic_via_os_replace
test_idempotency_corrupt_json_treated_as_empty_with_warning
test_idempotency_verify_still_detects_duplicate_nonce
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_store_concurrency_and_idempotency.py tests/test_memory_*.py tests/test_hosted_cron*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/memory/store.py src/proseforge_agent/cron/core.py tests/test_store_concurrency_and_idempotency.py
git commit -m "fix: cross-thread memory store and atomic idempotency store"
```

## Failure Modes To Prove

- Second-thread `.add()` does not raise.
- Two concurrent `remember` calls both persist; no lost update.
- A truncated nonce file does not crash `verify()`; it warns and continues.
- Duplicate-nonce detection still works after the changes.

## Verification

```powershell
python -m pytest tests/test_store_concurrency_and_idempotency.py -q
python -m pytest -q
```

## Acceptance

- `MemoryStore` is cross-thread safe; writes serialize under `FileLock`.
- `IdempotencyStore` is atomic and race-free; corrupt files fail soft.
- Full suite green; new tests added.

## Commit Boundary

Commit only the store/cron concurrency fixes and their tests. (Low-severity
findings 2.3 `FileLock` no-op and 2.4 retry string-match are NOT in scope —
see the deferred-findings note in 203.)
