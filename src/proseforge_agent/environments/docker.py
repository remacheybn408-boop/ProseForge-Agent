"""Docker execution backend planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .base import ExecutionCapabilities


@dataclass(frozen=True)
class DockerPlan:
    status: str
    dry_run: bool
    image: str
    mounts: list[dict[str, str]] = field(default_factory=list)
    env_allowlist: list[str] = field(default_factory=list)
    cleanup_plan: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DockerExecutionBackend:
    """Dry-run Docker backend with deterministic unavailable mode."""

    def __init__(self, *, workspace_root: str | Path, docker_available: bool = False) -> None:
        self.environment_id = "docker"
        self.workspace_root = Path(workspace_root).resolve()
        self.docker_available = docker_available
        self.capabilities = ExecutionCapabilities(
            filesystem_sync=True,
            long_running_process=False,
            network=False,
            gpu=False,
        )

    def check(
        self,
        *,
        image: str = "python:3.11",
        dry_run: bool = True,
        env_allowlist: list[str] | None = None,
    ) -> DockerPlan:
        status = "ready" if self.docker_available else "unavailable"
        reason = "docker is available" if self.docker_available else "docker is not available"
        return DockerPlan(
            status=status,
            dry_run=dry_run,
            image=image,
            mounts=[{"host": str(self.workspace_root), "container": "/workspace", "mode": "rw"}],
            env_allowlist=list(env_allowlist or []),
            cleanup_plan=["remove temporary container", "clear transient mounts"],
            reason=reason,
        )


__all__ = ["DockerExecutionBackend", "DockerPlan"]
