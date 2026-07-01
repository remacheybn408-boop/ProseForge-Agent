"""Plugin platform primitives."""

from .discovery import DiscoveredPlugin, PluginDiscovery
from .manifest import PluginManifest
from .manager import PluginActionResult, PluginManager
from .permissions import PLUGIN_PERMISSIONS, PluginPermissionDecision, PluginPermissionPolicy

__all__ = [
    "PLUGIN_PERMISSIONS",
    "DiscoveredPlugin",
    "PluginActionResult",
    "PluginDiscovery",
    "PluginManager",
    "PluginManifest",
    "PluginPermissionDecision",
    "PluginPermissionPolicy",
]
