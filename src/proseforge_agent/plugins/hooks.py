"""Lifecycle hooks exposed to plugins."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any


SUPPORTED_PLUGIN_HOOKS = (
    "on_agent_start",
    "on_project_open",
    "on_before_draft",
    "on_after_draft",
    "on_before_review",
    "on_after_review",
    "on_before_export",
    "on_after_export",
    "on_notification",
    "on_approval_created",
)

PluginHookHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class PluginHookError:
    hook: str
    error: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PluginHookResult:
    hook: str
    status: str
    dispatched: int
    errors: list[PluginHookError] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["errors"] = [error.to_dict() for error in self.errors]
        return data


@dataclass(frozen=True)
class PluginAPI:
    hooks: "PluginHookRegistry"


class PluginHookRegistry:
    """Register and dispatch plugin lifecycle handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[PluginHookHandler]] = {hook: [] for hook in SUPPORTED_PLUGIN_HOOKS}

    def register(self, hook: str, handler: PluginHookHandler) -> None:
        self._require_hook(hook)
        self._handlers[hook].append(handler)

    def emit(self, hook: str, event: dict[str, Any] | None = None) -> PluginHookResult:
        self._require_hook(hook)
        dispatched = 0
        errors: list[PluginHookError] = []
        payload = event or {}
        for handler in self._handlers[hook]:
            try:
                handler(payload)
                dispatched += 1
            except Exception as exc:  # noqa: BLE001 - plugin handlers are isolated from the host.
                errors.append(PluginHookError(hook=hook, error=str(exc)))
        status = "ok" if not errors else ("failed" if dispatched == 0 else "partial")
        return PluginHookResult(hook=hook, status=status, dispatched=dispatched, errors=errors)

    def on_agent_start(self, handler: PluginHookHandler) -> None:
        self.register("on_agent_start", handler)

    def on_project_open(self, handler: PluginHookHandler) -> None:
        self.register("on_project_open", handler)

    def on_before_draft(self, handler: PluginHookHandler) -> None:
        self.register("on_before_draft", handler)

    def on_after_draft(self, handler: PluginHookHandler) -> None:
        self.register("on_after_draft", handler)

    def on_before_review(self, handler: PluginHookHandler) -> None:
        self.register("on_before_review", handler)

    def on_after_review(self, handler: PluginHookHandler) -> None:
        self.register("on_after_review", handler)

    def on_before_export(self, handler: PluginHookHandler) -> None:
        self.register("on_before_export", handler)

    def on_after_export(self, handler: PluginHookHandler) -> None:
        self.register("on_after_export", handler)

    def on_notification(self, handler: PluginHookHandler) -> None:
        self.register("on_notification", handler)

    def on_approval_created(self, handler: PluginHookHandler) -> None:
        self.register("on_approval_created", handler)

    @staticmethod
    def _require_hook(hook: str) -> None:
        if hook not in SUPPORTED_PLUGIN_HOOKS:
            raise ValueError(f"unsupported plugin hook: {hook}")


__all__ = [
    "PluginAPI",
    "PluginHookError",
    "PluginHookHandler",
    "PluginHookRegistry",
    "PluginHookResult",
    "SUPPORTED_PLUGIN_HOOKS",
]
