"""MCP credentials boundary and redaction helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from .registry import MCPServerConfig


_SENSITIVE_KEYS = {"api_key", "apikey", "token", "secret", "password", "authorization"}
_ASSIGNMENT_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)=\S+")
_SECRET_TOKEN_RE = re.compile(r"\b(?:sk|tok)-[A-Za-z0-9_-]+")


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
    """Redact secrets from logs, approval payloads, and summaries."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if _is_sensitive_key(lowered):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        return _SECRET_TOKEN_RE.sub("[redacted]", _ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[redacted]", value))
    return value


def _is_sensitive_key(key: str) -> bool:
    return (
        key in _SENSITIVE_KEYS
        or key.endswith("_token")
        or key.endswith("-token")
        or key.endswith("_secret")
        or key.endswith("-secret")
        or key.endswith("_password")
        or key.endswith("-password")
    )


__all__ = ["MCPCredentialBoundary", "redact_sensitive"]
