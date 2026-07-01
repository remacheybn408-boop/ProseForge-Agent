"""Plugin platform primitives."""

from .discovery import DiscoveredPlugin, PluginDiscovery
from .manifest import PluginManifest

__all__ = ["DiscoveredPlugin", "PluginDiscovery", "PluginManifest"]
