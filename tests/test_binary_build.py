"""Real standalone binary build tests (Task 184)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.binary_build import BinaryBuilder, BuildReport
from proseforge_agent.install.binary_packaging import BinaryManifest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "standalone-binary-build"


@dataclass
class FakeRunner:
    exit_codes: list[int] = field(default_factory=list)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int:
        self.calls.append(list(argv))
        if not self.exit_codes:
            return 0
        return self.exit_codes.pop(0)


def _sample_manifest() -> BinaryManifest:
    payload = json.loads(FIXTURE_DIR.joinpath("manifest_sample.json").read_text(encoding="utf-8"))
    return BinaryManifest(
        platform=payload["platform"],
        arch=payload["arch"],
        smoke_command=list(payload["smoke_command"]),
        entry_point=payload["entry_point"],
        bundled_files=tuple(payload["bundled_files"]),
    )


def test_build_command_matches_manifest_entry_point_and_name():
    manifest = _sample_manifest()
    builder = BinaryBuilder(manifest=manifest, runner=FakeRunner())

    argv = builder.build_command()
    joined = " ".join(argv)

    assert "pyinstaller" in argv[0].lower() or argv[0] == "pyinstaller"
    assert "--onefile" in argv
    assert "--name" in argv
    name_index = argv.index("--name")
    assert argv[name_index + 1] == "pf-agent-windows-x64"
    assert "proseforge_agent.cli:main" in joined or "proseforge_agent" in joined
    assert any(part.endswith(".exe") or "pf-agent" in part for part in argv)
    assert argv.count("--add-data") == 2  # LICENSE + pyproject.toml


def test_build_blocked_when_manifest_invalid():
    manifest = BinaryManifest(platform="linux", arch="x64", smoke_command=[])
    runner = FakeRunner()
    builder = BinaryBuilder(manifest=manifest, runner=runner)

    report = builder.build()

    assert isinstance(report, BuildReport)
    assert report.passed is False
    assert "manifest" in report.summary
    assert runner.calls == []
    assert report.smoke_ok is False


def test_smoke_failure_marks_build_not_passed():
    manifest = _sample_manifest()
    runner = FakeRunner(exit_codes=[0, 1])  # build ok, smoke fails
    builder = BinaryBuilder(manifest=manifest, runner=runner)

    report = builder.build()

    assert report.passed is False
    assert report.smoke_ok is False
    assert "smoke" in report.summary
    assert len(runner.calls) == 2


def test_dry_run_does_not_invoke_real_pyinstaller():
    manifest = _sample_manifest()
    runner = FakeRunner()
    builder = BinaryBuilder(manifest=manifest, runner=runner)

    report = builder.build(dry_run=True)

    assert report.passed is True
    assert report.smoke_ok is True
    assert runner.calls == []
    assert any("dry_run" in step for step in report.steps)
    assert report.artifact_name == "pf-agent-windows-x64.exe"


def test_unknown_platform_or_arch_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        BinaryManifest(platform="beos", arch="x64")
    with pytest.raises(ConfigurationError):
        BinaryManifest(platform="linux", arch="ppc")


def test_report_paths_are_portable():
    manifest = _sample_manifest()
    runner = FakeRunner(exit_codes=[0, 0])
    builder = BinaryBuilder(manifest=manifest, runner=runner)

    report = builder.build()

    for step in report.steps:
        assert ":\\" not in step  # no windows absolute drive prefix
        assert not step.startswith("/Users/")
        assert not step.startswith("/home/")
    assert ":\\" not in report.summary
    assert report.artifact_name == manifest.artifact_name


def test_build_succeeds_when_build_and_smoke_ok():
    manifest = _sample_manifest()
    runner = FakeRunner(exit_codes=[0, 0])
    builder = BinaryBuilder(manifest=manifest, runner=runner)

    report = builder.build()

    assert report.passed is True
    assert report.smoke_ok is True
    assert len(runner.calls) == 2
    assert runner.calls[1] == ["pf-agent", "--version"]


def test_build_command_add_data_uses_platform_separator():
    win_manifest = BinaryManifest(platform="windows", arch="x64")
    linux_manifest = BinaryManifest(platform="linux", arch="x64")

    win_argv = BinaryBuilder(manifest=win_manifest, runner=FakeRunner()).build_command()
    linux_argv = BinaryBuilder(manifest=linux_manifest, runner=FakeRunner()).build_command()

    win_add_data = [win_argv[i + 1] for i, arg in enumerate(win_argv) if arg == "--add-data"]
    linux_add_data = [linux_argv[i + 1] for i, arg in enumerate(linux_argv) if arg == "--add-data"]

    for entry in win_add_data:
        assert ";" in entry
    for entry in linux_add_data:
        assert ":" in entry
