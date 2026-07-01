"""Real PyInstaller build runner for the standalone binary (Task 184).

The builder derives the PyInstaller argv from the Task 48 :class:`BinaryManifest`
and runs it through an injectable command runner so tests stay deterministic
and offline. After the build, the manifest's ``smoke_command``
(``pf-agent --version`` by default) gates success.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from ..errors import ConfigurationError
from .binary_packaging import BinaryManifest


class _Runner(Protocol):
    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int: ...


@dataclass(frozen=True)
class BuildReport:
    """Outcome of a binary build with portable, redacted details."""

    passed: bool
    artifact_name: str
    steps: list[str] = field(default_factory=list)
    smoke_ok: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BinaryBuilder:
    """Turn a :class:`BinaryManifest` into a real PyInstaller invocation."""

    def __init__(
        self,
        manifest: BinaryManifest,
        runner: _Runner,
        *,
        entry_script_resolver: Callable[[BinaryManifest], str] | None = None,
    ) -> None:
        self.manifest = manifest
        self._runner = runner
        self._entry_script_resolver = entry_script_resolver or _default_entry_script

    def build_command(self) -> list[str]:
        manifest = self.manifest
        stem = _artifact_stem(manifest.artifact_name)
        separator = ";" if manifest.platform == "windows" else ":"
        argv: list[str] = [
            "pyinstaller",
            "--onefile",
            "--name",
            stem,
            "--distpath",
            "dist",
            "--workpath",
            "build",
            "--specpath",
            "build",
        ]
        for bundled in manifest.bundled_files:
            argv.extend(["--add-data", f"{bundled}{separator}."])
        argv.append(self._entry_script_resolver(manifest))
        return argv

    def build(self, *, dry_run: bool = False) -> BuildReport:
        manifest = self.manifest
        artifact_name = manifest.artifact_name
        steps: list[str] = []

        manifest_report = manifest.validate()
        if manifest_report.status != "ok":
            failures = ", ".join(manifest_report.failures) or "invalid"
            return BuildReport(
                passed=False,
                artifact_name=artifact_name,
                steps=steps + [f"manifest_check: fail ({failures})"],
                smoke_ok=False,
                summary=f"manifest invalid: {failures}",
            )
        steps.append("manifest_check: ok")

        build_command = self.build_command()
        smoke_command = list(manifest.smoke_command)

        if dry_run:
            steps.append(f"build: dry_run -> {' '.join(build_command)}")
            steps.append(f"smoke: dry_run -> {' '.join(smoke_command)}")
            summary = f"dry_run build plan for {artifact_name}"
            return BuildReport(
                passed=True,
                artifact_name=artifact_name,
                steps=steps,
                smoke_ok=True,
                summary=summary,
            )

        build_exit = self._runner.run(build_command)
        steps.append(f"build: exit={build_exit}")
        if build_exit != 0:
            return BuildReport(
                passed=False,
                artifact_name=artifact_name,
                steps=steps,
                smoke_ok=False,
                summary=f"build failed with exit code {build_exit}",
            )

        smoke_exit = self._runner.run(smoke_command)
        steps.append(f"smoke: exit={smoke_exit}")
        smoke_ok = smoke_exit == 0
        if not smoke_ok:
            return BuildReport(
                passed=False,
                artifact_name=artifact_name,
                steps=steps,
                smoke_ok=False,
                summary=f"smoke command failed with exit code {smoke_exit}",
            )

        return BuildReport(
            passed=True,
            artifact_name=artifact_name,
            steps=steps,
            smoke_ok=True,
            summary=f"built {artifact_name} and smoke command passed",
        )


def _artifact_stem(artifact_name: str) -> str:
    if artifact_name.endswith(".exe"):
        return artifact_name[:-4]
    return artifact_name


def _default_entry_script(manifest: BinaryManifest) -> str:
    module_path = manifest.entry_point.split(":", 1)[0]
    return module_path.replace(".", "/") + ".py"


__all__ = ["BinaryBuilder", "BuildReport"]
