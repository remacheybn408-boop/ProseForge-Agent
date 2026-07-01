"""Singularity execution backend planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .base import ExecutionCapabilities


@dataclass(frozen=True)
class SingularityPlan:
    status: str
    dry_run: bool
    image: str
    command_prefix: list[str] = field(default_factory=list)
    unsupported_capabilities: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SingularityExecutionBackend:
    """Dry-run Singularity backend."""

    def __init__(self, *, singularity_available: bool = False) -> None:
        self.environment_id = "singularity"
        self.singularity_available = singularity_available
        self.capabilities = ExecutionCapabilities(filesystem_sync=True, long_running_process=False, network=False, gpu=False)

    def check(self, *, image: str, dry_run: bool = True) -> SingularityPlan:
        status = "ready" if self.singularity_available else "unavailable"
        reason = "singularity binary is available" if self.singularity_available else "singularity binary is not available"
        return SingularityPlan(
            status=status,
            dry_run=dry_run,
            image=image,
            command_prefix=["singularity", "exec", image],
            unsupported_capabilities=[] if self.singularity_available else ["gpu", "network"],
            reason=reason,
        )


__all__ = ["SingularityExecutionBackend", "SingularityPlan"]
