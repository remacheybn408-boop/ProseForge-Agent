"""Plugin platform primitives."""

from .dependencies import PluginDependencyIssue, PluginDependencyManager, PluginDependencyReport
from .discovery import DiscoveredPlugin, PluginDiscovery
from .manifest import PluginManifest
from .manager import PluginActionResult, PluginManager
from .permissions import PLUGIN_PERMISSIONS, PluginPermissionDecision, PluginPermissionPolicy
from .sandbox import PluginSandbox, PluginSandboxAPI, PluginSandboxPolicy, PluginSandboxResult

__all__ = [
    "PLUGIN_PERMISSIONS",
    "DiscoveredPlugin",
    "PluginDependencyIssue",
    "PluginDependencyManager",
    "PluginDependencyReport",
    "PluginActionResult",
    "PluginDiscovery",
    "PluginManager",
    "PluginManifest",
    "PluginPermissionDecision",
    "PluginPermissionPolicy",
    "PluginSandbox",
    "PluginSandboxAPI",
    "PluginSandboxPolicy",
    "PluginSandboxResult",
]
