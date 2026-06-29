"""Validate the GitHub Actions CI workflow against the native QA matrix.

The CI workflow promises that the test suite runs on Windows, macOS, and Linux.
This module parses ``.github/workflows/ci.yml`` and lets that promise be tested
without pushing to CI: it exposes the OS / Python matrix axes, confirms a pytest
step exists and runs after the package is installed, and cross-checks the OS axis
against the native QA matrix (Task 59) so the two cannot silently drift apart.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..errors import ConfigurationError

# Map a native QA platform name to the substring of its GitHub runner label.
_PLATFORM_RUNNER = {"windows": "windows", "macos": "macos", "linux": "ubuntu"}


class CIWorkflow:
    """Parsed view of a GitHub Actions workflow used to validate the CI matrix."""

    def __init__(self, document: dict) -> None:
        self._doc = document or {}

    @classmethod
    def from_text(cls, text: str) -> "CIWorkflow":
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ConfigurationError("CI workflow is not a valid YAML mapping")
        return cls(loaded)

    @classmethod
    def load(cls, path: str | Path) -> "CIWorkflow":
        workflow_path = Path(path)
        if not workflow_path.exists():
            raise ConfigurationError(f"CI workflow not found: {workflow_path}")
        return cls.from_text(workflow_path.read_text(encoding="utf-8"))

    def _matrix_job(self) -> dict:
        for job in (self._doc.get("jobs") or {}).values():
            if isinstance(job, dict) and "matrix" in (job.get("strategy") or {}):
                return job
        raise ConfigurationError("CI workflow has no job with a strategy matrix")

    def matrix(self) -> dict:
        """Return the parsed ``os`` and ``python-version`` matrix axes."""
        matrix = self._matrix_job()["strategy"]["matrix"]
        return {
            "os": list(matrix.get("os", [])),
            "python-version": [str(v) for v in matrix.get("python-version", [])],
        }

    def _steps(self) -> list[dict]:
        return [s for s in self._matrix_job().get("steps", []) if isinstance(s, dict)]

    def _run_commands(self) -> list[str]:
        return [str(step.get("run", "")) for step in self._steps()]

    def has_pytest_step(self) -> bool:
        """True if any step runs ``pytest``."""
        return any("pytest" in command for command in self._run_commands())

    def installs_package_before_tests(self) -> bool:
        """True if the package is pip-installed before the pytest step runs."""
        install_index = pytest_index = None
        for index, command in enumerate(self._run_commands()):
            if "pip install" in command and ("." in command):
                install_index = index if install_index is None else install_index
            if "pytest" in command and pytest_index is None:
                pytest_index = index
        return (
            install_index is not None
            and pytest_index is not None
            and install_index < pytest_index
        )

    def validate_against_qa_matrix(self, qa_matrix) -> None:
        """Raise :class:`ConfigurationError` if a QA-required OS is absent from CI."""
        if hasattr(qa_matrix, "to_dict"):
            platforms = list(qa_matrix.to_dict()["platforms"].keys())
        else:
            platforms = list(qa_matrix["platforms"].keys())
        os_axis = " ".join(self.matrix()["os"]).lower()
        missing = [
            platform
            for platform in platforms
            if _PLATFORM_RUNNER.get(platform, platform) not in os_axis
        ]
        if missing:
            raise ConfigurationError(
                "CI matrix is missing required QA platforms: " + ", ".join(sorted(missing))
            )


__all__ = ["CIWorkflow"]
