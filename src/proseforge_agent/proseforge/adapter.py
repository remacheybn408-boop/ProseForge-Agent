"""Safe subprocess adapter for the existing ProseForge engine.

The Agent orchestrates ProseForge; it never copies or imports the engine. All
engine paths derive from the configured root. Commands are always built in
list form (no shell string assembly) so quoting is correct on Windows, macOS,
and Linux, and ``--project-root`` is always supplied.

Discovery is non-fatal: a missing script is a warning for inspection. A
mutating action against a missing script is an error.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from ..errors import EngineAdapterError
from .results import EngineActionResult, EngineDiscovery

_SCRIPTS_DIR = "plugin/proseforge-codex/scripts"
_PROJECT_SCRIPT = "nf_project.py"
_PIPELINE_SCRIPT = "nf_pipeline.py"


class ProseForgeAdapter:
    """Detect and call the ProseForge engine under a configured root."""

    def __init__(
        self,
        root: str | Path,
        *,
        python_executable: str = sys.executable,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.root = Path(root)
        self.python_executable = python_executable
        self.timeout_seconds = timeout_seconds

    # -- discovery -------------------------------------------------------

    def _script_path(self, name: str) -> Path:
        return self.root / _SCRIPTS_DIR / name

    def discover(self) -> EngineDiscovery:
        """Report which engine scripts exist. Never raises on missing scripts."""
        project = self._script_path(_PROJECT_SCRIPT)
        pipeline = self._script_path(_PIPELINE_SCRIPT)
        return EngineDiscovery(
            root=self.root,
            root_exists=self.root.exists(),
            has_project_script=project.is_file(),
            has_pipeline_script=pipeline.is_file(),
            scripts={"project": project, "pipeline": pipeline},
        )

    # -- command construction --------------------------------------------

    def _build_command(
        self, script: Path, action: str, args: Sequence[str]
    ) -> list[str]:
        return [
            self.python_executable,
            str(script),
            action,
            "--project-root",
            str(self.root),
            *args,
        ]

    # -- execution -------------------------------------------------------

    def run_project_action(
        self,
        action: str,
        args: Sequence[str] = (),
        *,
        dry_run: bool = True,
    ) -> EngineActionResult:
        return self._run(self._script_path(_PROJECT_SCRIPT), action, args, dry_run)

    def run_pipeline_action(
        self,
        action: str,
        args: Sequence[str] = (),
        *,
        dry_run: bool = True,
    ) -> EngineActionResult:
        return self._run(self._script_path(_PIPELINE_SCRIPT), action, args, dry_run)

    def _run(
        self,
        script: Path,
        action: str,
        args: Sequence[str],
        dry_run: bool,
    ) -> EngineActionResult:
        command = self._build_command(script, action, list(args))

        if dry_run:
            # Render the command without touching the engine, even if the
            # script is missing (inspection is allowed to be incomplete).
            return EngineActionResult(command=command, status="dry_run")

        if not script.is_file():
            raise EngineAdapterError(
                f"cannot run mutating action {action!r}: engine script not found "
                f"at {script}"
            )

        started = time.monotonic()
        try:
            completed = subprocess.run(  # noqa: S603 - list form, no shell
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise EngineAdapterError(
                f"engine action {action!r} timed out after {self.timeout_seconds}s"
            ) from exc
        except OSError as exc:
            raise EngineAdapterError(
                f"failed to launch engine action {action!r}: {exc}"
            ) from exc
        duration = time.monotonic() - started

        stdout = completed.stdout or ""
        payload = self._try_parse_json(stdout)
        status = "ok" if completed.returncode == 0 else "error"
        return EngineActionResult(
            command=command,
            status=status,
            returncode=completed.returncode,
            stdout=stdout,
            stderr=completed.stderr or "",
            payload=payload,
            duration_seconds=duration,
        )

    @staticmethod
    def _try_parse_json(stdout: str) -> dict | None:
        text = stdout.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None


__all__ = ["ProseForgeAdapter"]
