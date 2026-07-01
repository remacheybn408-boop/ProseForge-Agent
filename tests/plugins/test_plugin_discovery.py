"""Plugin discovery tests (Task 144)."""

from __future__ import annotations

import json

from proseforge_agent.plugins import PluginDiscovery
from proseforge_agent.cli import main


def _write_manifest(root, plugin_id="example-plugin"):
    plugin_dir = root / plugin_id
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(
        f"""
plugin:
  id: {plugin_id}
  name: Example Plugin
  version: 0.1.0
  description: Example plugin
  entrypoint: plugin.main:register
""".strip(),
        encoding="utf-8",
    )
    return plugin_dir


def test_plugin_discovery_lists_local_plugin_directory(tmp_path):
    plugins_dir = tmp_path / "plugins"
    _write_manifest(plugins_dir)

    discovery = PluginDiscovery(local_dirs=[plugins_dir])
    plugins = discovery.discover()

    assert [plugin.id for plugin in plugins] == ["example-plugin"]
    assert discovery.info("example-plugin").manifest.name == "Example Plugin"


def test_plugin_discovery_reads_registry_index(tmp_path):
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"plugins": [{"id": "remote-plugin", "name": "Remote", "version": "1.0.0"}]}), encoding="utf-8")

    plugins = PluginDiscovery(registry_index=registry).discover()

    assert plugins[0].id == "remote-plugin"
    assert plugins[0].source == "registry"


def test_plugin_discovery_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_manifest(tmp_path / ".pf-agent" / "plugins")

    assert main(["plugin", "discover"]) == 0
    assert main(["plugin", "list"]) == 0
    assert main(["plugin", "info", "example-plugin"]) == 0

    out = capsys.readouterr().out
    assert "Plugins" in out
    assert "example-plugin" in out
