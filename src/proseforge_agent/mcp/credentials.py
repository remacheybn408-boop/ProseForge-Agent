"""MCP credentials boundary and redaction helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..agent.events import _redact as _events_redact
from .registry import MCPServerConfig


class MCPCredentialBoundary:
    """Build the exact environment an MCP server may receive."""

    def __init__(self, *, secret_resolver: Callable[[str], str] | None = None) -> None:
        self.secret_resolver = secret_resolver or (lambda _ref: "")

    def build_env(
        self,
        config: MCPServerConfig,
        *,
        source_env: dict[str, str] | None = None,
    ) -> dict[str, str]:
        source_env = source_env or {}
        env: dict[str, str] = dict(config.env or {})
        for key in config.env_allow or []:
            if key in source_env:
                env[key] = source_env[key]
        for key, ref in (config.secret_refs or {}).items():
            env[key] = self.secret_resolver(ref)
        return env


def redact_sensitive(value: Any) -> Any:
    """Redact secrets from logs, approval payloads, and summaries.

    Delegates to the canonical redactor in ``agent/events.py`` so there is a
    single source of truth (finding 3.1). Scans both dict keys and string
    values at every depth.
    """
    return _events_redact(value)


__all__ = ["MCPCredentialBoundary", "redact_sensitive"]
