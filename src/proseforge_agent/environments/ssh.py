"""SSH execution backend planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .base import ExecutionCapabilities


@dataclass(frozen=True)
class SSHPlan:
    status: str
    dry_run: bool
    profile: str
    connection: dict[str, str] = field(default_factory=dict)
    command_prefix: list[str] = field(default_factory=list)
    sync_plan: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SSHBackendPlanner:
    """Planner only: emits an :class:`SSHPlan` and never opens a connection."""

    def __init__(self, *, ssh_available: bool = False) -> None:
        self.environment_id = "ssh"
        self.ssh_available = ssh_available
        self.capabilities = ExecutionCapabilities(filesystem_sync=True, long_running_process=True, network=True, gpu=False)

    def check(self, *, profile: str, host: str = "", token: str = "", dry_run: bool = True) -> SSHPlan:
        status = "ready" if self.ssh_available else "unavailable"
        reason = "ssh binary is available" if self.ssh_available else "ssh binary is not available"
        return SSHPlan(
            status=status,
            dry_run=dry_run,
            profile=profile,
            connection={"host": "[redacted]" if host else "", "token": "[redacted]" if token else ""},
            command_prefix=["ssh", profile],
            sync_plan=["stage scoped project files", "pull artifact refs"],
            reason=reason,
        )


__all__ = ["SSHBackendPlanner", "SSHPlan"]
