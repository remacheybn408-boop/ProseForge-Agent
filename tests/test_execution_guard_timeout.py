"""ExecutionGuard enforcing (real) timeout (Task 200, finding 1.1)."""

from __future__ import annotations

import threading
import time

from proseforge_agent.agent.execution_guard import ExecutionGuard, ExecutionPolicy


def test_run_returns_timeout_when_func_blocks():
    guard = ExecutionGuard(ExecutionPolicy(timeout_seconds=0.05, max_retries=0))
    started = threading.Event()

    def hang():
        started.set()
        time.sleep(5)  # would hang the runtime under the old post-hoc check
        return "never"

    began = time.monotonic()
    result = guard.run("dep", hang)
    elapsed = time.monotonic() - began

    assert started.wait(1.0)
    assert result.ok is False
    assert result.status == "timeout"
    assert elapsed < 2.0  # returned control well before the 5s sleep finished


def test_run_succeeds_within_timeout_returns_output():
    guard = ExecutionGuard(ExecutionPolicy(timeout_seconds=1.0))
    result = guard.run("dep", lambda: "fast")
    assert result.ok is True
    assert result.output == "fast"


def test_blocking_timeout_retries_when_attempts_remain():
    guard = ExecutionGuard(ExecutionPolicy(timeout_seconds=0.05, max_retries=1, backoff_seconds=0.0))
    calls = {"n": 0}

    def sometimes_hangs():
        calls["n"] += 1
        if calls["n"] == 1:
            time.sleep(5)  # first attempt times out
            return "late"
        return "second-ok"

    result = guard.run("dep", sometimes_hangs)
    assert result.ok is True
    assert result.output == "second-ok"
    assert result.attempts == 2


def test_error_inside_worker_is_still_reported_as_error():
    guard = ExecutionGuard(ExecutionPolicy(timeout_seconds=1.0, max_retries=0))

    def boom():
        raise RuntimeError("kaboom")

    result = guard.run("dep", boom)
    assert result.ok is False
    assert result.status == "error"
    assert "kaboom" in result.error
