"""Extension foundation.

Opt-in, versioned, isolated plug-in points for providers, prompts, memory
backends, retrievers, gates, and more. See ``docs/developer-extensions.md`` for
the contract and a worked example.
"""

from .base import (
    EXTENSION_POINTS,
    Extension,
    ExtensionError,
    GateExtension,
    version_satisfies,
)
from .registry import ExtensionRegistry

__all__ = [
    "EXTENSION_POINTS",
    "Extension",
    "GateExtension",
    "ExtensionError",
    "version_satisfies",
    "ExtensionRegistry",
]
