"""First-run bootstrap auto-trigger detector (Task 188).

Answers one question for the bare ``pf-agent`` router: given the current
environment, should we auto-run onboarding before launching the chat REPL?

The detector is read-only: ``decide()`` inspects config, workspace, and a
consent marker but never mutates anything. ``complete_first_run()`` is the
one write helper — it stamps the versioned consent marker so subsequent runs
skip onboarding.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MARKER_NAME = ".first-run-completed.json"
MARKER_VERSION = 1

SKIP = "SKIP"
ONBOARD_MINIMAL = "ONBOARD_MINIMAL"
ONBOARD_FULL = "ONBOARD_FULL"

_SKIP_ENV = "PF_AGENT_SKIP_FIRST_RUN"


@dataclass(frozen=True)
class BootstrapDecision:
    """Verdict for whether to auto-run onboarding."""

    verdict: str
    reason: str = ""
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "reason": self.reason, "missing": list(self.missing)}


class AutoBootstrap:
    """Decide whether the bare command should onboard before the REPL."""

    def __init__(
        self,
        root: str | Path = ".pf-agent",
        *,
        app_dirs: Any | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.root = Path(root)
        self.app_dirs = app_dirs
        self.env = env if env is not None else os.environ

    def marker_path(self) -> Path:
        if self.app_dirs is not None and getattr(self.app_dirs, "config_dir", None):
            return Path(self.app_dirs.config_dir) / MARKER_NAME
        return self.root / MARKER_NAME

    def _marker_ok(self) -> bool:
        path = self.marker_path()
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False  # corrupt marker => treat as absent, re-onboard
        return isinstance(payload, dict) and bool(payload.get("version"))

    def decide(self) -> BootstrapDecision:
        if str(self.env.get(_SKIP_ENV, "")).strip() not in {"", "0", "false", "False"}:
            return BootstrapDecision(SKIP, reason=f"skip requested via {_SKIP_ENV} env")

        if self._marker_ok():
            return BootstrapDecision(SKIP, reason="first-run already completed")

        from ..setup.first_run import FirstRunBootstrap

        verdict = FirstRunBootstrap(self.root).check()
        if verdict.ready:
            # Ready but never stamped a marker (e.g. externally provisioned).
            return BootstrapDecision(SKIP, reason="workspace is already configured")

        config_exists = (self.root / "config.yaml").exists()
        if config_exists:
            return BootstrapDecision(
                ONBOARD_MINIMAL,
                reason="workspace exists but provider/setup is incomplete",
                missing=list(verdict.reasons),
            )
        return BootstrapDecision(
            ONBOARD_FULL,
            reason="fresh machine; no workspace config found",
            missing=list(verdict.reasons) or ["config missing"],
        )


def complete_first_run(root: str | Path) -> Path:
    """Stamp the versioned consent marker so future runs skip onboarding."""
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    marker = root_path / MARKER_NAME
    marker.write_text(json.dumps({"version": MARKER_VERSION}) + "\n", encoding="utf-8")
    return marker


__all__ = [
    "AutoBootstrap",
    "BootstrapDecision",
    "MARKER_NAME",
    "MARKER_VERSION",
    "ONBOARD_FULL",
    "ONBOARD_MINIMAL",
    "SKIP",
    "complete_first_run",
]
