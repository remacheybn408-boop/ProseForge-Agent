"""Restricted runtime helpers for plugin execution."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(slots=True)
class PluginSandboxPolicy:
    """Defines the narrow API surface exposed to a plugin."""

    project_root: Path | str
    timeout_seconds: float = 30.0
    memory_limit_mb: int | None = None
    secrets: dict[str, str] = field(default_factory=dict)
    expose_secrets: bool = False
    permissions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve()


@dataclass(slots=True)
class PluginSandboxResult:
    status: str
    value: Any = None
    error: str = ""
    timed_out: bool = False


class PluginSandboxAPI:
    """Project-scoped API available to sandboxed plugin code."""

    def __init__(self, policy: PluginSandboxPolicy) -> None:
        self._policy = policy

    def _resolve_project_path(self, relative_path: str | Path) -> Path | None:
        candidate = (Path(self._policy.project_root) / Path(relative_path)).resolve()
        try:
            candidate.relative_to(self._policy.project_root)
        except ValueError:
            return None
        return candidate

    def read_file(self, relative_path: str | Path) -> str | None:
        path = self._resolve_project_path(relative_path)
        if path is None or not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str | Path, text: str) -> bool:
        if not self._allows_any("write_files", "write_project"):
            return False
        path = self._resolve_project_path(relative_path)
        if path is None:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True

    def get_secret(self, name: str) -> str | None:
        if not self._policy.expose_secrets or not self._allows_any("secrets_access"):
            return None
        return self._policy.secrets.get(name)

    def _allows_any(self, *permissions: str) -> bool:
        declared = set(self._policy.permissions)
        return any(permission in declared for permission in permissions)


class PluginSandbox:
    """Runs plugin callables behind a restricted API and isolates failures."""

    def __init__(self, policy: PluginSandboxPolicy) -> None:
        self.policy = policy
        self.api = PluginSandboxAPI(policy)

    def run(self, callback: Callable[[PluginSandboxAPI], Any]) -> PluginSandboxResult:
        if self.policy.memory_limit_mb is not None:
            return PluginSandboxResult(
                status="failed",
                error="memory_limit_mb is unsupported by the in-process plugin sandbox",
            )

        result_queue: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

        def target() -> None:
            try:
                result_queue.put(("ok", callback(self.api)))
            except Exception as exc:  # noqa: BLE001 - plugins must not crash the host.
                result_queue.put(("failed", exc))

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=max(0.0, self.policy.timeout_seconds))
        if thread.is_alive():
            return PluginSandboxResult(
                status="failed",
                error=f"plugin exceeded timeout of {self.policy.timeout_seconds:g}s",
                timed_out=True,
            )
        status, value = result_queue.get()
        if status == "failed":
            return PluginSandboxResult(status="failed", error=str(value))
        return PluginSandboxResult(status="ok", value=value)
