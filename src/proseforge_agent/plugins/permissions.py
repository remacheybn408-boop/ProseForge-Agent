"""Plugin permission declarations and runtime checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..errors import ConfigurationError
from .manifest import PluginManifest

PLUGIN_PERMISSIONS = {
    "read_project",
    "write_project",
    "read_memory",
    "write_memory",
    "read_bible",
    "write_bible",
    "read_files",
    "write_files",
    "network_access",
    "provider_call",
    "mcp_access",
    "secrets_access",
    "shell_access",
    "write_artifacts",
}


@dataclass(frozen=True)
class PluginPermissionDecision:
    """Decision for one plugin permission request."""

    plugin_id: str
    permission: str
    allowed: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


class PluginPermissionPolicy:
    """Check runtime plugin capability requests against manifest declarations."""

    def check(self, manifest: PluginManifest, permission: str) -> PluginPermissionDecision:
        if permission not in PLUGIN_PERMISSIONS:
            raise ConfigurationError(f"unknown plugin permission: {permission}")
        declared = set(manifest.permissions)
        unknown_declared = declared.difference(PLUGIN_PERMISSIONS)
        if unknown_declared:
            raise ConfigurationError(f"unknown plugin permission: {', '.join(sorted(unknown_declared))}")
        allowed = permission in declared
        return PluginPermissionDecision(
            plugin_id=manifest.id,
            permission=permission,
            allowed=allowed,
            reason="declared in plugin manifest" if allowed else "permission not declared in plugin manifest",
        )


__all__ = ["PLUGIN_PERMISSIONS", "PluginPermissionDecision", "PluginPermissionPolicy"]
