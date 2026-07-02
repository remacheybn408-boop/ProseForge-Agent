"""Version policy + PyPI published-version lookup tests (Task 189)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.release.version_policy import (
    PyPIPublishedVersions,
    VersionPolicy,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "pypi-first-publish-and-version-bump"


def _fake_fetch(url: str) -> dict:
    if "test.pypi.org" in url:
        return json.loads((FIXTURE_DIR / "testpypi_index.json").read_text(encoding="utf-8"))
    return json.loads((FIXTURE_DIR / "pypi_index.json").read_text(encoding="utf-8"))


def test_version_policy_bumps_patch_minor_major():
    assert VersionPolicy("0.1.0").next("patch") == "0.1.1"
    assert VersionPolicy("0.1.0").next("minor") == "0.2.0"
    assert VersionPolicy("0.1.0").next("major") == "1.0.0"


def test_version_policy_prerelease():
    assert VersionPolicy("0.1.0").next("prerelease", pre_id="rc") == "0.1.1rc1"
    assert VersionPolicy("0.1.0rc1").next("prerelease", pre_id="rc") == "0.1.0rc2"


def test_version_policy_rejects_malformed_version():
    with pytest.raises(ConfigurationError):
        VersionPolicy("0.1").next("patch")
    with pytest.raises(ConfigurationError):
        VersionPolicy("not-a-version").next("patch")


def test_version_policy_refuses_duplicate():
    with pytest.raises(ConfigurationError):
        VersionPolicy("0.1.0").refuse_duplicate("0.1.0", {"0.1.0", "0.0.9"})
    # non-duplicate is fine (no raise)
    VersionPolicy("0.1.0").refuse_duplicate("0.1.1", {"0.1.0"})


def test_published_versions_parses_testpypi_index():
    lookup = PyPIPublishedVersions(fetch_json=_fake_fetch)
    versions = lookup.for_repository("testpypi")
    assert "0.1.0" in versions
    assert "0.0.9" in versions


def test_published_versions_parses_pypi_index():
    lookup = PyPIPublishedVersions(fetch_json=_fake_fetch)
    versions = lookup.for_repository("pypi")
    assert versions == {"0.0.9"}


def test_published_versions_unknown_repository_raises():
    lookup = PyPIPublishedVersions(fetch_json=_fake_fetch)
    with pytest.raises(ConfigurationError):
        lookup.for_repository("nowhere")


def test_published_versions_fail_open_on_fetch_error():
    def boom(url: str) -> dict:
        raise OSError("network down")

    lookup = PyPIPublishedVersions(fetch_json=boom)
    assert lookup.for_repository("pypi") == set()


def test_cli_release_bump_prints_next_version(capsys):
    exit_code = main(["release", "bump", "--kind", "patch"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "0.1.0" in out
    assert "0.1.1" in out


def test_cli_release_bump_write_updates_pyproject(tmp_path, monkeypatch, capsys):
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[project]\nname = "proseforge-agent"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    exit_code = main(["release", "bump", "--kind", "minor", "--write"])
    assert exit_code == 0
    assert 'version = "0.2.0"' in project.read_text(encoding="utf-8")


def test_cli_release_publish_dry_run_reports_plan(capsys):
    exit_code = main(["release", "publish", "--repository", "testpypi", "--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out.lower()
    assert "testpypi" in out
