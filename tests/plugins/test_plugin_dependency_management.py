"""Plugin dependency management tests (Task 148)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.plugins import PluginDependencyManager


def _plugin_source(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "plugin.yaml").write_text(
        """
plugin:
  id: dependency-plugin
  name: Dependency Plugin
  version: 0.1.0
  description: Plugin with Python dependencies
  entrypoint: plugin.main:register
  dependencies:
    python:
      - definitely-missing-proseforge-package>=1
      - demo-lib==2.0
""".strip(),
        encoding="utf-8",
    )
    return root


def test_plugin_dependency_management_contract(tmp_path):
    source = _plugin_source(tmp_path / "source")
    manager = PluginDependencyManager(tmp_path / "agent", installed_versions={"demo-lib": "1.0"})

    report = manager.check(source)

    assert report.plugin_id == "dependency-plugin"
    assert report.status == "blocked"
    assert any(issue.kind == "missing" for issue in report.issues)
    assert any(issue.kind == "version_conflict" and issue.dependency == "demo-lib==2.0" for issue in report.issues)
    assert "pip install 'definitely-missing-proseforge-package>=1'" in report.install_commands
    assert report.isolated_venv_supported is False


def test_plugin_dependency_mixed_version_parts_report_conflict(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "plugin.yaml").write_text(
        """
plugin:
  id: dependency-plugin
  name: Dependency Plugin
  version: 0.1.0
  description: Plugin with mixed version dependency
  entrypoint: plugin.main:register
  dependencies:
    python:
      - demo-lib>=1.0
""".strip(),
        encoding="utf-8",
    )
    manager = PluginDependencyManager(tmp_path / "agent", installed_versions={"demo-lib": "1.a"})

    report = manager.check(source)

    assert report.status == "blocked"
    assert any(issue.kind == "version_conflict" for issue in report.issues)


def test_plugin_deps_cli_reports_install_suggestion(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = _plugin_source(tmp_path / "source")
    assert main(["plugin", "install", str(source)]) == 0

    assert main(["plugin", "deps", "check", "dependency-plugin"]) == 0

    out = capsys.readouterr().out
    assert "Plugin Dependencies" in out
    assert "definitely-missing-proseforge-package>=1" in out
    assert "pip install" in out
