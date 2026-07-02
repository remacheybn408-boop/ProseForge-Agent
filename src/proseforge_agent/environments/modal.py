"""Modal-style execution backend planning."""

from __future__ import annotations

from .serverless import ServerlessPlan, build_serverless_plan


class ModalBackendPlanner:
    """Planner only: emits a :class:`ServerlessPlan` and never invokes Modal."""

    environment_id = "modal"

    def __init__(self, *, config: dict[str, str] | None = None, fake_state: str = "ready") -> None:
        self.config = dict(config or {})
        self.fake_state = fake_state

    def check(self, *, dry_run: bool = True) -> ServerlessPlan:
        return build_serverless_plan(backend="modal", config=self.config, fake_state=self.fake_state, dry_run=dry_run)


__all__ = ["ModalBackendPlanner"]
