# Task 200: ExecutionGuard Real (Enforcing) Timeout / 执行护栏真实超时

## Goal

Make `ExecutionGuard.run` enforce its timeout instead of measuring it after the
fact. Today (`agent/execution_guard.py:57`) the guard calls `func()`
synchronously and only checks `elapsed > timeout_seconds` **after `func`
returns** — a blocked/hung `func` never returns, so the timeout never fires and
the whole runtime can hang. Wrap the call so a stuck provider/MCP/tool call is
actually aborted at the timeout.

## Architecture Notes

Fixes **finding 1.1** (High · Correctness) of
`docs/review/core-review-2026-07-01.md`.

Verified current behavior: the retry loop does `output = func()` then
`elapsed = self._time() - start; if elapsed > self.policy.timeout_seconds:` —
a stopwatch report, not enforcement. Combined with `max_retries=0` default, a
socket read that never returns hangs forever.

Design:

- Use `concurrent.futures.ThreadPoolExecutor` (a single-worker executor per
  call, or an injected one): `future = executor.submit(func);
  output = future.result(timeout=self.policy.timeout_seconds)`.
- On `concurrent.futures.TimeoutError`: record a timeout failure
  (`status="timeout"`), cancel the future best-effort, and either retry (if
  attempts remain) or return the failure `ExecutionGuardResult`.
- Keep the existing seams: `time_fn` / `sleep_fn` stay injectable; add an
  optional `executor_factory` (or `run_with_timeout`) seam so tests can drive
  timeout deterministically **without real sleeping**.
- Preserve all existing result fields (`status`, `attempts`,
  `elapsed_seconds`, `recovery`) and circuit-breaker / rate-limit behavior.
- Optional: add `async def arun(...)` using `asyncio.wait_for` for async
  callers (only if a caller needs it; otherwise defer).

Note: Python threads cannot be force-killed; `future.cancel()` will not
interrupt an already-running `func`. Document this honestly — the guard
**returns** to the caller at the timeout (unblocking the runtime) even though
the orphaned thread may run to completion. That is the correct, achievable
semantics and matches the reviewer's fix direction.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (finding 1.1)
- 65-provider-usage-metering-and-budget.md / the ExecutionGuard card
  (63/64 range — tool timeout / rate limit / circuit breaker)
- `src/proseforge_agent/agent/execution_guard.py`

## Files

- Modify `src/proseforge_agent/agent/execution_guard.py` (`run`, add timeout
  enforcement + optional executor seam).
- Add tests in `tests/test_execution_guard_timeout.py`.

## Interfaces / Contracts

- `ExecutionGuard.run(key, func)` returns within ~`timeout_seconds` even if
  `func` blocks, with `status="timeout"`.
- Existing `ExecutionGuardResult` fields and circuit-breaker/rate-limit paths
  unchanged.
- A deterministic test seam exists so no test sleeps for a real timeout.

## Data Flow

1. `run("openai", provider.chat)` submits `func` to an executor.
2. `future.result(timeout=…)` returns output, or raises `TimeoutError`.
3. Timeout → structured failure returned; runtime is not blocked.

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_execution_guard_timeout.py::test_run_returns_timeout_when_func_blocks`**

```python
def test_run_returns_timeout_when_func_blocks():
    guard = ExecutionGuard(ExecutionPolicy(timeout_seconds=0.05, max_retries=0))
    started = threading.Event()

    def hang():
        started.set()
        time.sleep(5)   # would hang the runtime under the old code

    result = guard.run("dep", hang)

    assert started.wait(1.0)
    assert result.ok is False
    assert result.status == "timeout"
```

- [ ] **Step 2: Run the targeted test and confirm failure** (old code blocks
  ~5s then reports; the test would hang / not return status="timeout").

- [ ] **Step 3: Implement enforcing timeout via ThreadPoolExecutor + timeout
  result; keep seams.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_run_succeeds_within_timeout_returns_output
test_timeout_retries_when_attempts_remain
test_timeout_records_failure_and_opens_circuit_after_threshold
test_existing_error_and_rate_limit_paths_unchanged
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_execution_guard_timeout.py tests/test_execution_guard*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/agent/execution_guard.py tests/test_execution_guard_timeout.py
git commit -m "fix: enforce real timeout in execution guard"
```

## Failure Modes To Prove

- A `func` that sleeps far past the timeout still returns control at the
  timeout with `status="timeout"`.
- A fast `func` returns its output normally.
- Circuit breaker opens after repeated timeouts per the existing policy.

## Verification

```powershell
python -m pytest tests/test_execution_guard_timeout.py -q
python -m pytest -q
```

## Acceptance

- `ExecutionGuard.run` enforces the timeout (returns control, does not hang).
- All existing guard tests pass; new timeout tests added; full suite green.
- Thread-cancellation caveat documented in the module.

## Commit Boundary

Commit only the execution-guard timeout change and its tests. Do not bundle the
store/idempotency work (201).
