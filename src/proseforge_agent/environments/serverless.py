"""Shared serverless environment planning helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SERVERLESS_STATES = {"missing_config", "ready", "waking", "running", "hibernating", "failed", "unavailable"}


@dataclass(frozen=True)
class ServerlessPlan:
    backend: str
    status: str
    state: str
    dry_run: bool
    credentials: dict[str, str] = field(default_factory=dict)
    lifecycle_plan: list[str] = field(default_factory=list)
    artifact_sync_plan: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_serverless_plan(*, backend: str, config: dict[str, str], fake_state: str, dry_run: bool) -> ServerlessPlan:
    state = fake_state if fake_state in SERVERLESS_STATES else "failed"
    status = "ok" if state in {"ready", "waking", "running", "hibernating"} else state
    if not config:
        status = "missing_config"
        state = "missing_config"
    credentials = {key: "[redacted]" for key in config}
    return ServerlessPlan(
        backend=backend,
        status=status,
        state=state,
        dry_run=dry_run,
        credentials=credentials,
        lifecycle_plan=["validate config", "wake workspace", "run command", "hibernate workspace"],
        artifact_sync_plan=["upload scoped inputs", "download artifact refs"],
        reason=f"{backend} fake-client lifecycle state: {state}",
    )


__all__ = ["SERVERLESS_STATES", "ServerlessPlan", "build_serverless_plan"]
