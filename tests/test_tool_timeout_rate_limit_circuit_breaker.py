"""Execution guard tests (Task 122)."""

from __future__ import annotations

from proseforge_agent.agent.execution_guard import ExecutionGuard, ExecutionPolicy


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_execution_guard_retries_then_succeeds():
    clock = FakeClock()
    guard = ExecutionGuard(
        ExecutionPolicy(max_retries=1, backoff_seconds=0.5),
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return "ok"

    result = guard.run("provider.fake", flaky)

    assert result.ok is True
    assert result.output == "ok"
    assert result.attempts == 2
    assert clock.now == 0.5


def test_execution_guard_rate_limits_calls():
    clock = FakeClock()
    guard = ExecutionGuard(
        ExecutionPolicy(rate_limit_per_minute=1),
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )

    first = guard.run("mcp.filesystem.read", lambda: "ok")
    second = guard.run("mcp.filesystem.read", lambda: "no")

    assert first.ok is True
    assert second.ok is False
    assert second.status == "rate_limited"


def test_execution_guard_timeout_and_circuit_breaker():
    clock = FakeClock()
    guard = ExecutionGuard(
        ExecutionPolicy(timeout_seconds=1.0, circuit_breaker_failures=2, circuit_breaker_cooldown=10),
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )

    def slow():
        clock.sleep(2.0)
        return "late"

    first = guard.run("tool.write", slow)
    second = guard.run("tool.write", slow)
    third = guard.run("tool.write", lambda: "blocked")

    assert first.status == "timeout"
    assert second.status == "timeout"
    assert third.status == "circuit_open"
    assert third.recovery == "wait for circuit breaker cooldown"

    clock.sleep(10)
    recovered = guard.run("tool.write", lambda: "ok")
    assert recovered.ok is True
