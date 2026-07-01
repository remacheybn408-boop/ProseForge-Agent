"""Plugin platform primitives."""

from .discovery import DiscoveredPlugin, PluginDiscovery
from .manifest import PluginManifest
from .manager import PluginActionResult, PluginManager

__all__ = ["DiscoveredPlugin", "PluginActionResult", "PluginDiscovery", "PluginManager", "PluginManifest"]
