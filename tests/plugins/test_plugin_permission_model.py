"""Plugin permission model tests (Task 146)."""

from __future__ import annotations

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.plugins import PluginManifest, PluginPermissionPolicy


def test_plugin_permission_policy_allows_declared_capability(tmp_path):
    manifest_path = tmp_path / "plugin.yaml"
    manifest_path.write_text(
        """
plugin:
  id: safe-plugin
  name: Safe
  version: 0.1.0
  description: Safe plugin
  entrypoint: plugin.main:register
  permissions:
    - read_project
    - write_files
""".strip(),
        encoding="utf-8",
    )
    manifest = PluginManifest.load(manifest_path)

    decision = PluginPermissionPolicy().check(manifest, "write_files")

    assert decision.allowed is True
    assert decision.permission == "write_files"


def test_plugin_permission_policy_denies_missing_and_unknown_permissions(tmp_path):
    manifest_path = tmp_path / "plugin.yaml"
    manifest_path.write_text(
        """
plugin:
  id: safe-plugin
  name: Safe
  version: 0.1.0
  description: Safe plugin
  entrypoint: plugin.main:register
  permissions:
    - read_project
""".strip(),
        encoding="utf-8",
    )
    manifest = PluginManifest.load(manifest_path)

    assert PluginPermissionPolicy().check(manifest, "secrets_access").allowed is False
    with pytest.raises(ConfigurationError, match="unknown plugin permission"):
        PluginPermissionPolicy().check(manifest, "root_access")
