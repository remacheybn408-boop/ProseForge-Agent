"""Plugin install/update/remove CLI tests (Task 145)."""

from __future__ import annotations

from proseforge_agent.plugins import PluginManager
from proseforge_agent.cli import main


def _plugin_source(root, version="0.1.0"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "plugin.yaml").write_text(
        f"""
plugin:
  id: example-plugin
  name: Example Plugin
  version: {version}
  description: Example plugin
  entrypoint: plugin.main:register
""".strip(),
        encoding="utf-8",
    )
    (root / "plugin.py").write_text("def register(): return None\n", encoding="utf-8")
    return root


def test_plugin_manager_installs_updates_disables_enables_and_removes(tmp_path):
    source = _plugin_source(tmp_path / "source")
    manager = PluginManager(tmp_path / "agent")

    installed = manager.install(source)
    disabled = manager.disable("example-plugin")
    enabled = manager.enable("example-plugin")
    updated = manager.update(_plugin_source(tmp_path / "source-v2", version="0.2.0"))
    removed = manager.remove("example-plugin")

    assert installed.status == "installed"
    assert disabled.status == "disabled"
    assert enabled.status == "enabled"
    assert updated.status == "updated"
    assert removed.status == "removed"
    assert (tmp_path / "agent" / "plugins" / ".backups").exists()
    assert not (tmp_path / "agent" / "plugins" / "example-plugin").exists()


def test_plugin_cli_install_update_remove_enable_disable(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = _plugin_source(tmp_path / "source")
    source_v2 = _plugin_source(tmp_path / "source-v2", version="0.2.0")

    assert main(["plugin", "install", str(source)]) == 0
    assert main(["plugin", "disable", "example-plugin"]) == 0
    assert main(["plugin", "enable", "example-plugin"]) == 0
    assert main(["plugin", "update", str(source_v2)]) == 0
    assert main(["plugin", "remove", "example-plugin"]) == 0

    out = capsys.readouterr().out
    assert "Plugin Action" in out
    assert "example-plugin" in out
