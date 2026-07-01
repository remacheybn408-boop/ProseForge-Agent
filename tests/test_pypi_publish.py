"""Real PyPI/TestPyPI publish runner tests (Task 183)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.package_checks import PackageCheck, PackageReport
from proseforge_agent.release.publish import (
    PublishPlan,
    PublishReport,
    PyPIPublisher,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pypi-publish"


@dataclass
class FakeRunner:
    """Deterministic command runner: records argv, returns pre-canned exit codes."""

    exit_codes: list[int] | None = None
    calls: list[list[str]] | None = None

    def __post_init__(self) -> None:
        if self.exit_codes is None:
            self.exit_codes = []
        if self.calls is None:
            self.calls = []

    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int:
        self.calls.append(list(argv))
        if not self.exit_codes:
            return 0
        return self.exit_codes.pop(0)


class PassingChecker:
    def verify(self) -> PackageReport:
        return PackageReport(
            checks=[PackageCheck("console_script", "ok", "pf-agent -> proseforge_agent.cli:main")],
            source="pyproject.toml",
        )


class FailingChecker:
    def verify(self) -> PackageReport:
        return PackageReport(
            checks=[
                PackageCheck("console_script", "ok", "pf-agent -> proseforge_agent.cli:main"),
                PackageCheck("dependencies", "fail", "no dependencies", recovery="declare deps"),
            ],
            source="pyproject.toml",
        )


def _version() -> str:
    return FIXTURE_DIR.joinpath("version_sample.txt").read_text(encoding="utf-8").strip()


def test_publish_plan_builds_and_uploads_to_selected_repository():
    publisher = PyPIPublisher(
        runner=FakeRunner(),
        checker=PassingChecker(),
        version_reader=_version,
    )
    plan = publisher.plan(repository="testpypi")

    assert plan.build_command[:3] == ["python", "-m", "build"]
    assert "--repository" in plan.upload_command
    assert "testpypi" in plan.upload_command
    assert plan.repository == "testpypi"
    assert plan.version == "0.42.1"


def test_publish_blocked_when_package_checker_fails():
    runner = FakeRunner()
    publisher = PyPIPublisher(runner=runner, checker=FailingChecker(), version_reader=_version)

    report = publisher.publish(repository="testpypi")

    assert isinstance(report, PublishReport)
    assert report.passed is False
    assert report.skipped is True
    assert "package_checks" in report.summary
    assert runner.calls == []


def test_publish_refused_when_version_already_exists():
    runner = FakeRunner()
    publisher = PyPIPublisher(
        runner=runner,
        checker=PassingChecker(),
        version_reader=_version,
        published_versions_lookup=lambda repository: {"0.42.1"},
    )

    report = publisher.publish(repository="testpypi")

    assert report.passed is False
    assert report.skipped is True
    assert "0.42.1" in report.summary
    assert "already published" in report.summary
    assert runner.calls == []


def test_dry_run_does_not_invoke_real_upload():
    runner = FakeRunner()
    publisher = PyPIPublisher(runner=runner, checker=PassingChecker(), version_reader=_version)

    report = publisher.publish(repository="pypi", dry_run=True)

    assert report.passed is True
    assert report.skipped is False
    assert report.repository == "pypi"
    assert runner.calls == []  # dry_run performs no real command
    assert any("dry_run" in step for step in report.steps)


def test_unknown_repository_raises_configuration_error():
    publisher = PyPIPublisher(runner=FakeRunner(), checker=PassingChecker(), version_reader=_version)
    with pytest.raises(ConfigurationError):
        publisher.publish(repository="nowhere")
    with pytest.raises(ConfigurationError):
        publisher.plan(repository="nowhere")


def test_report_and_logs_never_contain_token(capsys):
    runner = FakeRunner()
    publisher = PyPIPublisher(
        runner=runner,
        checker=PassingChecker(),
        version_reader=_version,
    )
    token = "pypi-AABBCCDDEE-supersecret"

    report = publisher.publish(
        repository="testpypi",
        dry_run=False,
        credentials={"TWINE_PASSWORD": token, "TWINE_USERNAME": "__token__"},
    )
    stdout = capsys.readouterr().out

    assert report.passed is True
    for step in report.steps:
        assert token not in step
    assert token not in report.summary
    assert token not in stdout
    for call in runner.calls:
        for arg in call:
            assert token not in arg


def test_publish_runs_build_then_upload_on_success():
    runner = FakeRunner(exit_codes=[0, 0])
    publisher = PyPIPublisher(runner=runner, checker=PassingChecker(), version_reader=_version)

    report = publisher.publish(repository="testpypi")

    assert report.passed is True
    assert len(runner.calls) == 2
    assert runner.calls[0][:3] == ["python", "-m", "build"]
    assert runner.calls[1][0] == "twine"
    assert "--repository" in runner.calls[1]
    assert "testpypi" in runner.calls[1]


def test_build_failure_stops_upload():
    runner = FakeRunner(exit_codes=[1])
    publisher = PyPIPublisher(runner=runner, checker=PassingChecker(), version_reader=_version)

    report = publisher.publish(repository="testpypi")

    assert report.passed is False
    assert len(runner.calls) == 1
    assert "build failed" in report.summary


def test_publish_plan_is_repository_specific():
    publisher = PyPIPublisher(runner=FakeRunner(), checker=PassingChecker(), version_reader=_version)
    testpypi_plan = publisher.plan(repository="testpypi")
    pypi_plan = publisher.plan(repository="pypi")

    assert "testpypi" in testpypi_plan.upload_command
    assert "pypi" in pypi_plan.upload_command
    assert testpypi_plan.upload_command != pypi_plan.upload_command
    assert isinstance(testpypi_plan, PublishPlan)
