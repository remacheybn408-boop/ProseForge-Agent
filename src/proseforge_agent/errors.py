"""Typed exceptions for ProseForge Agent.

Every error raised by this package inherits :class:`ProseForgeAgentError`,
so callers can catch the whole family with a single ``except`` clause.

Only the boundaries that exist today are defined here. Memory and retrieval
error types are introduced by the tasks that add those subsystems.
"""

from __future__ import annotations


class ProseForgeAgentError(Exception):
    """Base class for all ProseForge Agent errors."""


class ConfigurationError(ProseForgeAgentError):
    """Raised when configuration is missing, invalid, or fails validation."""


class EngineAdapterError(ProseForgeAgentError):
    """Raised when a call into the ProseForge engine fails."""


class ProviderError(ProseForgeAgentError):
    """Raised when an LLM provider call fails."""


class MemoryError(ProseForgeAgentError):
    """Raised when a memory store operation fails validation or persistence."""


__all__ = [
    "ProseForgeAgentError",
    "ConfigurationError",
    "EngineAdapterError",
    "ProviderError",
    "MemoryError",
]
