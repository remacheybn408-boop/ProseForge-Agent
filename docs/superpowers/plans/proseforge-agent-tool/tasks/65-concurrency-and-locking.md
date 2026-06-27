# Task 65: Concurrency And Locking

## Goal

Protect the agent database and workflow state from concurrent writers so chat, background jobs, and workflow runs cannot corrupt shared data.

## Agent Product Requirement

Once chat, background jobs, and the local API can run at the same time, shared state must stay consistent under concurrent access.

> Dependency note: execute after the memory store (Task 07), workflow state (Task 12), and event bus / background jobs (Task 40). Logical position: 40.5.

## Architecture Notes

`concurrency` provides one shared locking primitive used by the memory store (`agent.db`) and the workflow state store. It offers a cross-platform advisory file lock and a SQLite busy/retry policy so writers serialize instead of clobbering each other. It is a low-level utility with no provider, workflow, or chat logic; those subsystems acquire a lock around their write paths. A writer that cannot acquire the lock within a timeout fails cleanly rather than corrupting data.

Read before starting:

- ../architecture/02-system-architecture.md (Acceptance Criteria: state written after every major step)
- ../architecture/04-deep-memory-and-retrieval.md
- ../architecture/06-workflow-engine.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/concurrency.py`
- Create `tests/test_concurrency_locking.py`
- Create `tests/fixtures/concurrency-and-locking/state_seed.json`

## Interfaces / Contracts

- `FileLock(path, timeout).acquire()` / `.release()` and a context-manager form.
- `with_sqlite_retry(callable, busy_timeout)` retries on `database is locked` within a bound.
- Two writers contending for the same lock serialize; the second waits, then proceeds, with no lost write.
- Acquisition that exceeds the timeout raises `ProseForgeAgentError` (a clean failure, not corruption).

## Data Flow

1. A writer requests the lock for a target file/db.
2. If free, it acquires and proceeds; if held, it waits up to the timeout.
3. SQLite writes use a busy-retry within the timeout.
4. The writer releases the lock when done.
5. On timeout, it raises a clean error and leaves data unchanged.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_concurrency_locking.py::test_two_writers_serialize_without_losing_writes`**

```python
def test_two_writers_serialize_without_losing_writes(tmp_path):
    target = tmp_path / "state.json"
    results = run_two_concurrent_writers(target, FileLock)
    assert results.both_committed is True
    assert results.final_count == 2  # neither write was lost
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_concurrency_locking.py::test_two_writers_serialize_without_losing_writes -q
```

Expected: FAIL because `FileLock` and the helpers are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `FileLock`, the context-manager form, and `with_sqlite_retry`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_concurrency_locking.py::test_two_writers_serialize_without_losing_writes -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_lock_timeout_raises_clean_error_without_corruption
test_sqlite_busy_is_retried_within_bound
test_lock_released_on_exception_in_context_manager
test_stale_lock_file_is_recoverable
test_lock_path_handles_utf8_and_spaces
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_concurrency_locking.py -q
python -m pytest tests/test_memory_store.py tests/test_workflow_state.py -q
```

Expected: the locking tests pass and the memory/workflow stores still pass with locking applied to their write paths.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/concurrency.py tests/test_concurrency_locking.py tests/fixtures/concurrency-and-locking
git commit -m "feat: add concurrency and locking"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The advisory file lock works on Windows, macOS, and Linux.
- Lock paths handle UTF-8 names and spaces.
- No platform-specific path assumptions.

## Failure Modes To Prove

- Two contending writers serialize with no lost write.
- A lock timeout raises a clean error and leaves data unchanged.
- SQLite `database is locked` is retried within a bound.
- The lock is released even if the writer raises inside the context manager.

## Verification

```powershell
python -m pytest tests/test_concurrency_locking.py -q
python -m pytest tests/test_memory_store.py tests/test_workflow_state.py -q
```

## Acceptance

- A shared cross-platform lock protects agent.db and workflow state.
- Concurrent writers serialize without corruption.
- Lock timeouts fail cleanly.
- Memory and workflow stores use the lock on their write paths.

## Commit Boundary

Commit only concurrency files and tests after verification passes. Wire the lock into the memory/workflow write paths only through their existing interfaces.
