"""Result types for the ProseForge engine adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EngineDiscovery:
    """What the adapter found at the configured ProseForge root."""

    root: Path
    root_exists: bool
    has_project_script: bool
    has_pipeline_script: bool
    scripts: dict[str, Path] = field(default_factory=dict)

    @property
    def is_usable(self) -> bool:
        """True only when both engine entry scripts are present."""
        return self.has_project_script and self.has_pipeline_script


@dataclass(frozen=True)
class EngineActionResult:
    """Outcome of one engine action.

    ``status`` is ``"dry_run"`` when the command was rendered but not executed,
    ``"ok"`` on a zero exit code, or ``"error"`` on a non-zero exit code. The
    raw ``stdout`` is always preserved; ``payload`` is the parsed JSON object
    when ``stdout`` is valid JSON, otherwise ``None``.
    """

    command: list[str]
    status: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    payload: dict | None = None
    artifacts: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


__all__ = ["EngineDiscovery", "EngineActionResult"]
