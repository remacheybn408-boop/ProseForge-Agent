import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.binary_packaging import BinaryManifest


FIXTURE = Path(__file__).parent / "fixtures" / "standalone-binary-packaging" / "manifest_sample.json"


def test_windows_artifact_name_ends_with_exe():
    assert BinaryManifest("windows", "x64").artifact_name == "pf-agent-windows-x64.exe"


def test_macos_and_linux_artifact_names_have_no_extension():
    assert BinaryManifest("macos", "arm64").artifact_name == "pf-agent-macos-arm64"
    assert BinaryManifest("linux", "x64").artifact_name == "pf-agent-linux-x64"


def test_manifest_includes_license_and_metadata_files():
    manifest = BinaryManifest("linux", "x64")
    assert "LICENSE" in manifest.bundled_files
    assert "pyproject.toml" in manifest.bundled_files
    assert manifest.entry_point == "proseforge_agent.cli:main"


def test_validate_fails_when_smoke_command_missing():
    report = BinaryManifest("linux", "x64", smoke_command=[]).validate()
    assert report.status == "fail"
    assert "smoke command missing" in report.failures


def test_unknown_platform_or_arch_raises_configuration_error():
    with pytest.raises(ConfigurationError):
        BinaryManifest("plan9", "x64")
    with pytest.raises(ConfigurationError):
        BinaryManifest("linux", "sparc")


def test_manifest_report_paths_are_portable():
    payload = BinaryManifest("linux", "x64").to_dict()
    assert "\\" not in "/".join(payload["bundled_files"])


def test_manifest_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["entry_point"] == "proseforge_agent.cli:main"
