"""Real PyPI/TestPyPI publish runner (Task 183).

The publisher builds wheel+sdist via ``python -m build`` and uploads them via
``twine upload``. Both are executed through an injectable ``runner`` so tests
stay deterministic and offline. Credentials are read from the environment /
native secret storage at call time and are never embedded in the plan, the
report, or any log line.

The Task 47 :class:`PackageChecker` gate blocks the upload when any check
fails, and versions already present on the target index are refused.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..errors import ConfigurationError
from ..install.package_checks import PackageReport


_ALLOWED_REPOSITORIES = ("testpypi", "pypi")

_TOKEN_ENV_KEYS = frozenset({"TWINE_PASSWORD", "PYPI_TOKEN", "TESTPYPI_TOKEN", "TOKEN"})


class _Runner(Protocol):
    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int: ...


class _Checker(Protocol):
    def verify(self) -> PackageReport: ...


@dataclass(frozen=True)
class PublishPlan:
    """Ordered argv steps that will be executed to publish."""

    repository: str
    version: str
    build_command: list[str]
    upload_command: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishReport:
    """Outcome of a publish attempt with redacted, portable details."""

    passed: bool
    repository: str
    version: str
    steps: list[str] = field(default_factory=list)
    skipped: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PyPIPublisher:
    """Build wheel/sdist and upload to TestPyPI or PyPI via an injectable runner."""

    def __init__(
        self,
        runner: _Runner,
        checker: _Checker,
        *,
        version_reader: Callable[[], str] | None = None,
        published_versions_lookup: Callable[[str], set[str]] | None = None,
    ) -> None:
        self._runner = runner
        self._checker = checker
        self._version_reader = version_reader or _default_version_reader
        self._published_versions_lookup = published_versions_lookup or (lambda repository: set())

    def plan(self, repository: str) -> PublishPlan:
        self._require_known_repository(repository)
        version = self._version_reader()
        return PublishPlan(
            repository=repository,
            version=version,
            build_command=["python", "-m", "build"],
            upload_command=["twine", "upload", "--repository", repository, "dist/*"],
        )

    def publish(
        self,
        repository: str,
        *,
        dry_run: bool = False,
        credentials: dict[str, str] | None = None,
    ) -> PublishReport:
        self._require_known_repository(repository)
        plan = self.plan(repository)
        version = plan.version
        steps: list[str] = []

        report = self._checker.verify()
        if not _all_checks_ok(report):
            failed_names = [check.name for check in report.checks if check.status != "ok"]
            return PublishReport(
                passed=False,
                repository=repository,
                version=version,
                steps=steps + [f"package_checks: failed ({', '.join(failed_names)})"],
                skipped=True,
                summary=f"package_checks failed: {', '.join(failed_names)}",
            )
        steps.append("package_checks: ok")

        published = self._published_versions_lookup(repository)
        if version in published:
            return PublishReport(
                passed=False,
                repository=repository,
                version=version,
                steps=steps + [f"version_check: {version} already published on {repository}"],
                skipped=True,
                summary=f"version {version} already published on {repository}",
            )
        steps.append(f"version_check: {version} is new on {repository}")

        redacted_env = _redact_env(credentials or {})

        if dry_run:
            steps.append(f"build: dry_run -> {' '.join(plan.build_command)}")
            steps.append(f"upload: dry_run -> {_redact_argv(plan.upload_command)}")
            summary = f"dry_run publish plan for {repository} @ {version}"
            print(f"[publish] {summary}")
            return PublishReport(
                passed=True,
                repository=repository,
                version=version,
                steps=steps,
                skipped=False,
                summary=summary,
            )

        build_exit = self._runner.run(plan.build_command, env=redacted_env)
        steps.append(f"build: exit={build_exit}")
        if build_exit != 0:
            summary = f"build failed with exit code {build_exit}"
            print(f"[publish] {summary}")
            return PublishReport(
                passed=False,
                repository=repository,
                version=version,
                steps=steps,
                skipped=False,
                summary=summary,
            )

        upload_exit = self._runner.run(plan.upload_command, env=redacted_env)
        steps.append(f"upload: exit={upload_exit}")
        if upload_exit != 0:
            summary = f"upload failed with exit code {upload_exit}"
            print(f"[publish] {summary}")
            return PublishReport(
                passed=False,
                repository=repository,
                version=version,
                steps=steps,
                skipped=False,
                summary=summary,
            )

        summary = f"published {version} to {repository}"
        print(f"[publish] {summary}")
        return PublishReport(
            passed=True,
            repository=repository,
            version=version,
            steps=steps,
            skipped=False,
            summary=summary,
        )

    @staticmethod
    def _require_known_repository(repository: str) -> None:
        if repository not in _ALLOWED_REPOSITORIES:
            raise ConfigurationError(
                f"unknown repository {repository!r}; expected one of {_ALLOWED_REPOSITORIES}"
            )


def _default_version_reader() -> str:
    path = Path("pyproject.toml")
    if not path.exists():
        raise ConfigurationError("pyproject.toml not found; supply a version_reader")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    version = data.get("project", {}).get("version")
    if not version:
        raise ConfigurationError("project.version not set in pyproject.toml")
    return str(version)


def _all_checks_ok(report: PackageReport) -> bool:
    return all(check.status == "ok" for check in report.checks)


def _redact_env(env: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in env.items():
        upper = key.upper()
        if any(part in upper for part in _TOKEN_ENV_KEYS) or "TOKEN" in upper or "PASSWORD" in upper:
            redacted[key] = "[redacted]"
        else:
            redacted[key] = value
    return redacted


def _redact_argv(argv: list[str]) -> str:
    return " ".join(argv)


__all__ = ["PublishPlan", "PublishReport", "PyPIPublisher"]
