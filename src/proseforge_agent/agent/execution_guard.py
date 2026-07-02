"""Shared timeout, retry, rate-limit, and circuit-breaker guard."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any


class _GuardTimeout(Exception):
    """Raised internally when a guarded call exceeds its wall-clock timeout."""


@dataclass(frozen=True)
class ExecutionPolicy:
    """Runtime guard policy for tool, MCP, web, and provider calls."""

    timeout_seconds: float = 30.0
    max_retries: int = 0
    backoff_seconds: float = 0.0
    rate_limit_per_minute: int | None = None
    circuit_breaker_failures: int = 3
    circuit_breaker_cooldown: float = 60.0


@dataclass(frozen=True)
class ExecutionGuardResult:
    """Result from a guarded call."""

    ok: bool
    status: str
    output: Any = None
    error: str = ""
    attempts: int = 0
    elapsed_seconds: float = 0.0
    recovery: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExecutionGuard:
    """Apply shared execution safety controls around a callable."""

    def __init__(
        self,
        policy: ExecutionPolicy | None = None,
        *,
        time_fn: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        timeout_runner: Callable[[Callable[[], Any], float], Any] | None = None,
    ) -> None:
        self.policy = policy or ExecutionPolicy()
        self._time = time_fn or time.monotonic
        self._sleep = sleep_fn or time.sleep
        # Seam so callers/tests can substitute the enforcing-timeout mechanism.
        self._timeout_runner = timeout_runner or _thread_timeout_runner
        self._rate_events: dict[str, deque[float]] = defaultdict(deque)
        self._failures: dict[str, int] = defaultdict(int)
        self._opened_at: dict[str, float] = {}

    def run(self, key: str, func: Callable[[], Any]) -> ExecutionGuardResult:
        now = self._time()
        if self._is_circuit_open(key, now):
            return ExecutionGuardResult(
                ok=False,
                status="circuit_open",
                attempts=0,
                recovery="wait for circuit breaker cooldown",
            )
        rate_limited = self._rate_limited(key, now)
        if rate_limited is not None:
            return rate_limited

        attempts = 0
        last_error = ""
        max_attempts = self.policy.max_retries + 1
        while attempts < max_attempts:
            attempts += 1
            start = self._time()
            try:
                # Enforcing timeout: a blocked/hung func is abandoned at the
                # deadline so it cannot hang the runtime (finding 1.1). The
                # orphaned worker runs on a daemon thread and dies with the
                # process — it cannot be force-killed (documented limitation).
                output = self._timeout_runner(func, self.policy.timeout_seconds)
            except _GuardTimeout:
                last_error = f"timeout after {self.policy.timeout_seconds:.3f}s"
                elapsed = self._time() - start
                if attempts < max_attempts:
                    self._sleep(self.policy.backoff_seconds)
                    continue
                self._record_failure(key)
                return ExecutionGuardResult(
                    ok=False,
                    status="timeout",
                    error=last_error,
                    attempts=attempts,
                    elapsed_seconds=elapsed,
                    recovery="increase timeout or narrow the call",
                )
            except Exception as exc:  # noqa: BLE001 - guard returns structured errors
                last_error = str(exc)
                elapsed = self._time() - start
                if attempts < max_attempts:
                    self._sleep(self.policy.backoff_seconds)
                    continue
                self._record_failure(key)
                return ExecutionGuardResult(
                    ok=False,
                    status="error",
                    error=last_error,
                    attempts=attempts,
                    elapsed_seconds=elapsed,
                    recovery="retry later or inspect the failing dependency",
                )
            elapsed = self._time() - start
            if elapsed > self.policy.timeout_seconds:
                last_error = f"timeout after {elapsed:.3f}s"
                if attempts < max_attempts:
                    self._sleep(self.policy.backoff_seconds)
                    continue
                self._record_failure(key)
                return ExecutionGuardResult(
                    ok=False,
                    status="timeout",
                    error=last_error,
                    attempts=attempts,
                    elapsed_seconds=elapsed,
                    recovery="increase timeout or narrow the call",
                )
            self._record_success(key)
            return ExecutionGuardResult(
                ok=True,
                status="ok",
                output=output,
                attempts=attempts,
                elapsed_seconds=elapsed,
            )
        self._record_failure(key)
        return ExecutionGuardResult(
            ok=False,
            status="error",
            error=last_error or "guard failed",
            attempts=attempts,
            recovery="retry later",
        )

    def _rate_limited(self, key: str, now: float) -> ExecutionGuardResult | None:
        limit = self.policy.rate_limit_per_minute
        if not limit:
            return None
        window = self._rate_events[key]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= limit:
            return ExecutionGuardResult(
                ok=False,
                status="rate_limited",
                attempts=0,
                recovery="wait for rate-limit window to reset",
            )
        window.append(now)
        return None

    def _is_circuit_open(self, key: str, now: float) -> bool:
        opened_at = self._opened_at.get(key)
        if opened_at is None:
            return False
        if now - opened_at >= self.policy.circuit_breaker_cooldown:
            self._opened_at.pop(key, None)
            self._failures[key] = 0
            return False
        return True

    def _record_failure(self, key: str) -> None:
        self._failures[key] += 1
        if self._failures[key] >= self.policy.circuit_breaker_failures:
            self._opened_at[key] = self._time()

    def _record_success(self, key: str) -> None:
        self._failures[key] = 0
        self._opened_at.pop(key, None)


def _thread_timeout_runner(func: Callable[[], Any], timeout: float) -> Any:
    """Run ``func`` on a daemon thread; raise :class:`_GuardTimeout` at deadline.

    A daemon thread is used so an abandoned (hung) call cannot block interpreter
    exit. The worker keeps running until it finishes on its own, but control
    returns to the caller at the timeout. Timeouts <= 0 mean "no enforced
    deadline" and run synchronously (preserves fake-clock timeout tests).
    """
    if timeout is None or timeout <= 0:
        return func()

    box: dict[str, Any] = {}
    done = threading.Event()

    def worker() -> None:
        try:
            box["value"] = func()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller thread
            box["error"] = exc
        finally:
            done.set()

    threading.Thread(target=worker, daemon=True).start()
    if not done.wait(timeout):
        raise _GuardTimeout(f"timeout after {timeout:.3f}s")
    if "error" in box:
        raise box["error"]
    return box.get("value")


__all__ = ["ExecutionGuard", "ExecutionGuardResult", "ExecutionPolicy"]
