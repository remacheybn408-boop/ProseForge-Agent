"""Plugin platform primitives."""

from .dependencies import PluginDependencyIssue, PluginDependencyManager, PluginDependencyReport
from .discovery import DiscoveredPlugin, PluginDiscovery
from .hooks import (
    SUPPORTED_PLUGIN_HOOKS,
    PluginAPI,
    PluginHookError,
    PluginHookRegistry,
    PluginHookResult,
)
from .harness import PluginTestHarness, PluginTestReport
from .manifest import PluginManifest
from .manager import PluginActionResult, PluginManager
from .permissions import PLUGIN_PERMISSIONS, PluginPermissionDecision, PluginPermissionPolicy
from .sandbox import PluginSandbox, PluginSandboxAPI, PluginSandboxPolicy, PluginSandboxResult

__all__ = [
    "PLUGIN_PERMISSIONS",
    "SUPPORTED_PLUGIN_HOOKS",
    "DiscoveredPlugin",
    "PluginAPI",
    "PluginDependencyIssue",
    "PluginDependencyManager",
    "PluginDependencyReport",
    "PluginHookError",
    "PluginHookRegistry",
    "PluginHookResult",
    "PluginTestHarness",
    "PluginTestReport",
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
