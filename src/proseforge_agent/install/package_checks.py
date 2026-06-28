"""Read-only checks for pip, pipx, and source installation."""

from __future__ import annotations

import importlib
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackageCheck:
    """One package installation check."""

    name: str
    status: str
    detail: str
    recovery: str | None = None


@dataclass(frozen=True)
class PackageReport:
    """Package installation report."""

    checks: list[PackageCheck]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source.replace("\\", "/"), "checks": [asdict(check) for check in self.checks]}


class PackageChecker:
    """Verify package metadata without invoking pip or the network."""

    def __init__(self, pyproject_path: str | Path = "pyproject.toml") -> None:
        self.pyproject_path = Path(pyproject_path)

    def console_scripts(self) -> dict[str, str]:
        data = self._load()
        return dict(data.get("project", {}).get("scripts", {}))

    def verify(self) -> PackageReport:
        data = self._load()
        project = data.get("project", {})
        scripts = self.console_scripts()
        checks = [
            PackageCheck(
                "console_script",
                "ok" if scripts.get("pf-agent") == "proseforge_agent.cli:main" else "fail",
                f"pf-agent -> {scripts.get('pf-agent')}",
                None if scripts.get("pf-agent") else "Declare [project.scripts].pf-agent",
            ),
            self._import_check(),
            PackageCheck(
                "dependencies",
                "ok" if project.get("dependencies") else "fail",
                ", ".join(project.get("dependencies", [])) or "no dependencies declared",
                None if project.get("dependencies") else "Declare runtime dependencies in pyproject.toml",
            ),
            self._python_version_check(project.get("requires-python", "")),
        ]
        return PackageReport(checks=checks, source=str(self.pyproject_path).replace("\\", "/"))

    def _load(self) -> dict[str, Any]:
        return tomllib.loads(self.pyproject_path.read_text(encoding="utf-8"))

    @staticmethod
    def _import_check() -> PackageCheck:
        try:
            importlib.import_module("proseforge_agent")
        except Exception as exc:  # noqa: BLE001
            return PackageCheck("import", "fail", str(exc), "Install package from source or pip")
        return PackageCheck("import", "ok", "proseforge_agent importable")

    @staticmethod
    def _python_version_check(requirement: str) -> PackageCheck:
        if requirement.startswith(">="):
            version = tuple(int(part) for part in requirement[2:].split(".")[:2])
            current = sys.version_info[:2]
            ok = current >= version
            return PackageCheck(
                "python_version",
                "ok" if ok else "fail",
                f"requires {requirement}; running {current[0]}.{current[1]}",
                None if ok else f"Install Python {version[0]}.{version[1]} or newer",
            )
        return PackageCheck("python_version", "warn", "no minimum declared", "Declare requires-python")


__all__ = ["PackageCheck", "PackageChecker", "PackageReport"]
