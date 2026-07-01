"""Desktop notification delivery channel."""

from __future__ import annotations

import platform as platform_module
from collections.abc import Callable

from .core import NotificationEvent

Runner = Callable[[list[str]], dict]


class DesktopNotificationChannel:
    """Cross-platform desktop notification channel with injectable command runner."""

    name = "desktop"

    def __init__(self, *, enabled: bool = True, platform: str | None = None, runner: Runner | None = None) -> None:
        self.enabled = enabled
        self.platform = (platform or platform_module.system()).lower()
        self.runner = runner

    def send(self, event: NotificationEvent) -> dict:
        if not self.enabled:
            return {"channel": self.name, "status": "skipped", "reason": "desktop notifications disabled"}
        command = self._command(event)
        if command is None:
            return {"channel": self.name, "status": "unsupported", "reason": f"unsupported platform: {self.platform}"}
        if self.runner is None:
            return {"channel": self.name, "status": "unsupported", "reason": "desktop notification runner is not configured"}
        result = self.runner(command)
        return {"channel": self.name, "status": "sent", "command": command, "result": result}

    def _command(self, event: NotificationEvent) -> list[str] | None:
        if self.platform.startswith("linux"):
            return ["notify-send", event.title, event.message]
        if self.platform.startswith("darwin") or self.platform.startswith("mac"):
            script = f'display notification "{_escape(event.message)}" with title "{_escape(event.title)}"'
            return ["osascript", "-e", script]
        if self.platform.startswith("win"):
            script = f'New-BurntToastNotification -Text "{_escape(event.title)}", "{_escape(event.message)}"'
            return ["powershell", "-NoProfile", "-Command", script]
        return None


def _escape(value: str) -> str:
    return value.replace('"', '\\"')


__all__ = ["DesktopNotificationChannel"]
