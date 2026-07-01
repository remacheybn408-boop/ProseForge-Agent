"""Base execution environment contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import monotonic
from typing import Any, Protocol


_SENSITIVE_KEY_PARTS = ("token", "secret", "password", "authorization", "api_key")


@dataclass(frozen=True)
class ExecutionCapabilities:
    filesystem_sync: bool = False
    long_running_process: bool = False
    network: bool = False
    gpu: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionResult:
    environment_id: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    timed_out: bool = False
    artifact_refs: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    capabilities: ExecutionCapabilities = field(default_factory=ExecutionCapabilities)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = self.capabilities.to_dict()
        return data


class ExecutionEnvironment(Protocol):
    environment_id: str
    capabilities: ExecutionCapabilities

    def run(
        self,
        command: list[str] | str,
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        ...


class FakeExecutionEnvironment:
    """Deterministic execution environment with no shell side effects."""

    def __init__(self, *, environment_id: str = "fake", stdout_limit: int = 4096) -> None:
        self.environment_id = environment_id
        self.stdout_limit = max(0, stdout_limit)
        self.capabilities = ExecutionCapabilities(
            filesystem_sync=True,
            long_running_process=True,
            network=False,
            gpu=False,
        )

    def run(
        self,
        command: list[str] | str,
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        started = monotonic()
        rendered = " ".join(command) if isinstance(command, list) else str(command)
        if timeout == 0:
            return ExecutionResult(
                environment_id=self.environment_id,
                stdout="",
                stderr="timeout",
                exit_code=124,
                duration_ms=_duration_ms(started),
                timed_out=True,
                env=_redact_env(env or {}),
                capabilities=self.capabilities,
            )
        stdout, truncated = _truncate(rendered, self.stdout_limit)
        return ExecutionResult(
            environment_id=self.environment_id,
            stdout=stdout,
            stderr="",
            exit_code=0,
            duration_ms=_duration_ms(started),
            stdout_truncated=truncated,
            env=_redact_env(env or {}),
            capabilities=self.capabilities,
        )


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit], True


def _redact_env(env: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in env.items():
        lowered = key.lower()
        redacted[key] = "[redacted]" if any(part in lowered for part in _SENSITIVE_KEY_PARTS) else str(value)
    return redacted


def _duration_ms(started: float) -> int:
    return max(0, int((monotonic() - started) * 1000))


__all__ = ["ExecutionCapabilities", "ExecutionEnvironment", "ExecutionResult", "FakeExecutionEnvironment"]
