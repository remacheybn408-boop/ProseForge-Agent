"""Plugin test harness tests (Task 150)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.plugins import PluginTestHarness


def _plugin_source(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "plugin.yaml").write_text(
        """
plugin:
  id: harness-plugin
  name: Harness Plugin
  version: 0.1.0
  description: Plugin used by the harness tests
  entrypoint: plugin:register
  permissions:
    - read_project
""".strip(),
        encoding="utf-8",
    )
    (root / "plugin.py").write_text(
        """
def register(plugin_api):
    plugin_api.hooks.on_after_draft(lambda event: event.setdefault("hook_seen", True))
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return root


def test_plugin_test_harness_contract(tmp_path):
    source = _plugin_source(tmp_path / "my-plugin")

    report = PluginTestHarness(work_root=tmp_path / "work").run(
        source,
        with_demo_project=True,
        hook="on_after_draft",
    )

    assert report.status == "ok"
    assert report.checks["manifest"] == "ok"
    assert report.checks["dependencies"] == "ok"
    assert report.checks["permissions"] == "ok"
    assert report.checks["import"] == "ok"
    assert report.checks["register"] == "ok"
    assert report.checks["hooks"] == "ok"
    assert report.checks["sandbox"] == "ok"
    assert report.hook_result is not None
    assert report.hook_result.dispatched == 1


def test_plugin_test_cli_runs_without_touching_real_project(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = _plugin_source(tmp_path / "my-plugin")

    assert main(["plugin", "test", str(source), "--with-demo-project", "--hook", "on_after_draft"]) == 0

    out = capsys.readouterr().out
    assert "Plugin Test Harness" in out
    assert "manifest=ok" in out
    assert "sandbox=ok" in out
