"""Local in-process API facade for agent integrations.

This module intentionally does not start a web server. It exposes the stable
request/response shapes a future transport can wrap.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from ..agent import AgentTurnRequest
from ..errors import ConfigurationError


_SECRET_KEYS = {"api_key", "apikey", "token", "secret", "password", "authorization"}


class LocalAgentService:
    """In-process facade for health, chat, sessions, provider, and workflow state."""

    def __init__(
        self,
        *,
        kernel,
        session_store,
        bind: str = "127.0.0.1",
        allow_remote: bool = False,
        permission_level: str = "read_only",
        provider_name: str = "fake",
    ) -> None:
        self.kernel = kernel
        self.session_store = session_store
        self.bind = bind
        self.allow_remote = allow_remote
        self.permission_level = permission_level
        self.provider_name = provider_name
        self._validate_bind()

    def health(self) -> dict[str, Any]:
        """Return local facade readiness without starting a listener."""
        return {
            "status": "ok",
            "bind": self.bind,
            "allow_remote": self.allow_remote,
            "permission_level": self.permission_level,
            "web_server": False,
        }

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run one kernel turn and return a redacted JSON-serializable result."""
        request = AgentTurnRequest(
            session_id=str(payload.get("session_id") or "service-check"),
            text=str(payload.get("message") or payload.get("text") or ""),
            mode=str(payload.get("mode") or "general_chat"),
            project_slug=payload.get("project"),
            permission_level=str(payload.get("permission_level") or self.permission_level),
        )
        result = self.kernel.run_turn(request)
        return _redact(_serializable(result))

    def sessions(self, *, project_slug: str | None = None) -> dict[str, Any]:
        """Return known sessions using the injected store."""
        rows = []
        if self.session_store is not None and hasattr(self.session_store, "list"):
            rows = self.session_store.list(project_slug=project_slug)
        return {"sessions": [_serializable(row) for row in rows]}

    def provider_status(self) -> dict[str, Any]:
        """Return provider status in the API response shape."""
        return {"providers": [{"name": self.provider_name, "status": "configured"}]}

    def workflow_status(self, run_id: str | None = None) -> dict[str, Any]:
        """Return workflow status without starting or mutating a workflow."""
        return {"run_id": run_id, "status": "not_started", "runnable": False}

    def _validate_bind(self) -> None:
        local_binds = {"127.0.0.1", "localhost", "::1"}
        if self.bind in local_binds:
            return
        if not self.allow_remote:
            raise ConfigurationError("remote service bind requires --allow-remote")
        if self.permission_level != "system_write":
            raise ConfigurationError("remote service bind requires system_write permission")


def _serializable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    if hasattr(value, "__dict__") and not isinstance(value, type):
        public = {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
        for key in (
            "id",
            "mode",
            "project_slug",
            "workflow_run_id",
            "title",
            "created_at",
            "updated_at",
        ):
            if key not in public and hasattr(value, key):
                public[key] = getattr(value, key)
        return _serializable(public)
    return value


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in _SECRET_KEYS:
                redacted[key] = "[redacted]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


__all__ = ["LocalAgentService"]
