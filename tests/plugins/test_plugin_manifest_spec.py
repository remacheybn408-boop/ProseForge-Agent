"""Plugin manifest spec tests (Task 143)."""

from __future__ import annotations

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.plugins import PluginManifest


def test_plugin_manifest_parses_standard_yaml(tmp_path):
    manifest_path = tmp_path / "plugin.yaml"
    manifest_path.write_text(
        """
plugin:
  id: proseforge-plugin-example
  name: Example Plugin
  version: 0.1.0
  description: Example plugin
  entrypoint: plugin.main:register
  permissions:
    - read_project
    - write_artifacts
  dependencies:
    python:
      - pydantic>=2
  compatible:
    proseforge_agent: ">=0.8.0"
""".strip(),
        encoding="utf-8",
    )

    manifest = PluginManifest.load(manifest_path)

    assert manifest.id == "proseforge-plugin-example"
    assert manifest.entrypoint == "plugin.main:register"
    assert manifest.permissions == ["read_project", "write_artifacts"]
    assert manifest.dependencies["python"] == ["pydantic>=2"]
    assert manifest.compatible["proseforge_agent"] == ">=0.8.0"


def test_plugin_manifest_rejects_missing_required_fields(tmp_path):
    manifest_path = tmp_path / "plugin.yaml"
    manifest_path.write_text("plugin:\n  id: missing-fields\n", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="missing required plugin field"):
        PluginManifest.load(manifest_path)


def test_plugin_manifest_rejects_path_escape_id(tmp_path):
    manifest_path = tmp_path / "plugin.yaml"
    manifest_path.write_text(
        """
plugin:
  id: ../outside
  name: Escape
  version: 0.1.0
  description: Unsafe id
  entrypoint: plugin:register
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="unsafe plugin id"):
        PluginManifest.load(manifest_path)
