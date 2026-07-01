"""Local execution backend."""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import Any

from .base import ExecutionCapabilities, ExecutionResult, _duration_ms, _redact_env


class LocalExecutionBackend:
    """Conservative local backend using an injected process runner."""

    def __init__(self, *, process_runner: Any, workspace_root: str | Path) -> None:
        self.environment_id = "local"
        self.process_runner = process_runner
        self.workspace_root = Path(workspace_root).resolve()
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
        resolved_cwd = _resolve_inside(self.workspace_root, cwd or ".")
        raw = self.process_runner.run(command, cwd=str(resolved_cwd), env=env or {}, timeout=timeout)
        return ExecutionResult(
            environment_id=self.environment_id,
            stdout=str(raw.get("stdout", "")),
            stderr=str(raw.get("stderr", "")),
            exit_code=int(raw.get("exit_code", 0)),
            duration_ms=_duration_ms(started),
            env=_redact_env(env or {}),
            capabilities=self.capabilities,
        )


def _resolve_inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"path escapes workspace: {relative}")
    return candidate


__all__ = ["LocalExecutionBackend"]
