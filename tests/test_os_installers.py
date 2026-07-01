"""OS installer builder and signing tests (Task 185)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.app_dirs import AppDirs
from proseforge_agent.install.installers import (
    InstallerBuilder,
    InstallerRecipe,
    InstallerReport,
)


@dataclass
class FakeRunner:
    exit_codes: list[int] = field(default_factory=list)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int:
        self.calls.append(list(argv))
        if not self.exit_codes:
            return 0
        return self.exit_codes.pop(0)


def _win_dirs() -> AppDirs:
    return AppDirs.for_platform(
        "windows",
        env={"APPDATA": "C:/Users/demo/AppData/Roaming", "LOCALAPPDATA": "C:/Users/demo/AppData/Local"},
    )


def _mac_dirs() -> AppDirs:
    return AppDirs.for_platform("macos", env={"HOME": "/Users/demo"})


def _linux_dirs() -> AppDirs:
    return AppDirs.for_platform("linux", env={"HOME": "/home/demo"})


def test_windows_recipe_produces_msi_and_uses_app_dirs_install_path():
    builder = InstallerBuilder(platform="windows", app_dirs=_win_dirs(), runner=FakeRunner())
    recipe = builder.recipe()

    assert recipe.artifact_name.endswith(".msi")
    assert recipe.install_dir
    assert recipe.sign_command
    assert recipe.sign_command[0] == "signtool"
    assert recipe.package_command[0] in {"candle", "light", "wix", "candle.exe"}


def test_macos_recipe_produces_dmg():
    builder = InstallerBuilder(platform="macos", app_dirs=_mac_dirs(), runner=FakeRunner())
    recipe = builder.recipe()

    assert recipe.artifact_name.endswith(".dmg")
    assert recipe.sign_command[0] == "codesign"
    assert recipe.package_command[0] in {"hdiutil", "create-dmg"}


def test_linux_recipe_produces_install_script():
    builder = InstallerBuilder(platform="linux", app_dirs=_linux_dirs(), runner=FakeRunner())
    recipe = builder.recipe()

    assert recipe.artifact_name == "install.sh"
    assert recipe.sign_command[0] == "gpg"
    assert recipe.package_command[0] in {"sh", "bash", "install.sh"} or "install.sh" in recipe.package_command


def test_signing_skipped_with_warning_when_no_credentials():
    runner = FakeRunner()
    builder = InstallerBuilder(
        platform="linux",
        app_dirs=_linux_dirs(),
        runner=runner,
        credential_reader=lambda name: None,
    )

    report = builder.build(sign=True)

    assert isinstance(report, InstallerReport)
    assert report.passed is True
    assert report.signed is False
    assert any("skipped" in step and "sign" in step for step in report.skipped)
    assert "warning" in report.summary.lower() or "unsigned" in report.summary.lower()


def test_dry_run_does_not_invoke_real_packager():
    runner = FakeRunner()
    builder = InstallerBuilder(
        platform="windows",
        app_dirs=_win_dirs(),
        runner=runner,
        credential_reader=lambda name: "cert-id-x",
    )

    report = builder.build(sign=True, dry_run=True)

    assert report.passed is True
    assert runner.calls == []
    assert any("dry_run" in step for step in report.steps)


def test_unknown_platform_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        InstallerBuilder(platform="beos", app_dirs=_linux_dirs(), runner=FakeRunner())


def test_recipe_and_report_never_contain_signing_secret():
    secret = "SIGNING-CERT-abc123"
    runner = FakeRunner(exit_codes=[0, 0])
    builder = InstallerBuilder(
        platform="windows",
        app_dirs=_win_dirs(),
        runner=runner,
        credential_reader=lambda name: secret,
    )

    recipe = builder.recipe()
    report = builder.build(sign=True)

    for arg in recipe.package_command + recipe.sign_command:
        assert secret not in arg
    for step in report.steps + report.skipped:
        assert secret not in step
    assert secret not in report.summary
    for call in runner.calls:
        for arg in call:
            assert secret not in arg


def test_signed_build_succeeds_when_credentials_present():
    runner = FakeRunner(exit_codes=[0, 0])
    builder = InstallerBuilder(
        platform="macos",
        app_dirs=_mac_dirs(),
        runner=runner,
        credential_reader=lambda name: "team-id-xyz",
    )

    report = builder.build(sign=True)

    assert report.passed is True
    assert report.signed is True
    assert len(runner.calls) == 2  # package + sign
    assert runner.calls[1][0] == "codesign"


def test_install_dir_matches_app_dirs_data_dir():
    dirs = _linux_dirs()
    builder = InstallerBuilder(platform="linux", app_dirs=dirs, runner=FakeRunner())
    recipe = builder.recipe()
    # install_dir should be a str path that starts with the AppDirs data_dir
    assert str(dirs.data_dir).replace("\\", "/") in recipe.install_dir.replace("\\", "/")


def test_package_failure_marks_report_not_passed():
    runner = FakeRunner(exit_codes=[1])
    builder = InstallerBuilder(
        platform="linux",
        app_dirs=_linux_dirs(),
        runner=runner,
        credential_reader=lambda name: "gpg-key",
    )

    report = builder.build(sign=True)

    assert report.passed is False
    assert report.signed is False
    assert "package" in report.summary.lower()
