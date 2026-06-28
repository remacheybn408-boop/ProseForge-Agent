"""Standalone binary packaging manifest."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..errors import ConfigurationError


_PLATFORMS = {"windows", "macos", "linux"}
_ARCHES = {"x64", "arm64"}


@dataclass(frozen=True)
class ManifestReport:
    """Validation result for a binary manifest."""

    status: str
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BinaryManifest:
    """Declarative standalone binary artifact metadata."""

    platform: str
    arch: str
    smoke_command: list[str] = field(default_factory=lambda: ["pf-agent", "--version"])
    entry_point: str = "proseforge_agent.cli:main"
    bundled_files: tuple[str, ...] = ("LICENSE", "pyproject.toml")

    def __post_init__(self) -> None:
        if self.platform not in _PLATFORMS:
            raise ConfigurationError(f"unknown binary platform {self.platform!r}")
        if self.arch not in _ARCHES:
            raise ConfigurationError(f"unknown binary architecture {self.arch!r}")

    @property
    def artifact_name(self) -> str:
        suffix = ".exe" if self.platform == "windows" else ""
        return f"pf-agent-{self.platform}-{self.arch}{suffix}"

    def validate(self) -> ManifestReport:
        failures = []
        if not self.smoke_command:
            failures.append("smoke command missing")
        if "LICENSE" not in self.bundled_files:
            failures.append("license missing")
        if "pyproject.toml" not in self.bundled_files:
            failures.append("metadata missing")
        return ManifestReport(status="fail" if failures else "ok", failures=failures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_name": self.artifact_name,
            "entry_point": self.entry_point,
            "bundled_files": list(self.bundled_files),
            "smoke_command": list(self.smoke_command),
        }


__all__ = ["BinaryManifest", "ManifestReport"]
