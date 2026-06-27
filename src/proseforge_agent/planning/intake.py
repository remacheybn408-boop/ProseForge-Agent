"""Project intake: the validated input to phase planning.

Intake captures the genre, market, length, cadence, tone, audience, and
constraints that shape a novel's phase plan. It is plain validated data and
needs no model access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..errors import ConfigurationError

_REQUIRED = ("slug", "title", "genre", "target_chapters")


@dataclass(frozen=True)
class ProjectIntake:
    """Validated intake for one novel project."""

    slug: str
    title: str
    genre: str
    target_chapters: int
    market: str = ""
    length: str = ""
    cadence: str = ""
    tone: str = ""
    audience: str = ""
    constraints: list[str] = field(default_factory=list)


def validate_intake(intake: ProjectIntake) -> None:
    """Raise ConfigurationError when required intake fields are missing/invalid."""
    for name in ("slug", "title", "genre"):
        if not getattr(intake, name):
            raise ConfigurationError(f"intake field {name!r} is required")
    if not intake.target_chapters or intake.target_chapters <= 0:
        raise ConfigurationError("intake field 'target_chapters' must be a positive integer")


def load_intake(path: str | Path) -> ProjectIntake:
    """Load and validate a project intake from a YAML file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigurationError(f"intake file {path} must be a mapping")
    for name in _REQUIRED:
        if data.get(name) in (None, ""):
            raise ConfigurationError(f"intake file {path} is missing required field {name!r}")
    intake = ProjectIntake(
        slug=data["slug"],
        title=data["title"],
        genre=data["genre"],
        target_chapters=int(data["target_chapters"]),
        market=data.get("market", ""),
        length=data.get("length", ""),
        cadence=data.get("cadence", ""),
        tone=data.get("tone", ""),
        audience=data.get("audience", ""),
        constraints=list(data.get("constraints") or []),
    )
    validate_intake(intake)
    return intake


__all__ = ["ProjectIntake", "validate_intake", "load_intake"]
