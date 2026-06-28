"""Uninstall planning with explicit data-retention boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..errors import ConfigurationError
from .app_dirs import AppDirs


@dataclass(frozen=True)
class UninstallResult:
    """Outcome of executing or validating an uninstall plan."""

    status: str
    actions: dict[str, list[str]]


@dataclass(frozen=True)
class UninstallPlan:
    """Read-only uninstall plan grouped by data sensitivity."""

    actions: dict[str, list[str]]
    retained_paths: list[str] = field(default_factory=list)
    remove_user_data: bool = False

    def execute(self, *, permission: str, confirmation_token: str | None = None) -> UninstallResult:
        if self.remove_user_data and (permission != "system_write" or confirmation_token != "REMOVE_USER_DATA"):
            raise ConfigurationError("removing user data requires system_write and REMOVE_USER_DATA confirmation")
        return UninstallResult(status="planned", actions=self.actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actions": self.actions,
            "retained_paths": self.retained_paths,
            "remove_user_data": self.remove_user_data,
        }


class UninstallPlanner:
    """Build uninstall plans without deleting files."""

    def __init__(self, app_dirs: AppDirs) -> None:
        self.app_dirs = app_dirs

    def plan(self, remove_user_data: bool = False) -> UninstallPlan:
        cache_logs = [str(self.app_dirs.cache_dir), str(self.app_dirs.log_dir)]
        user_data = [str(self.app_dirs.data_dir), str(self.app_dirs.config_dir)]
        actions = {
            "binaries": ["pf-agent"],
            "shell_integration": ["profile.d/proseforge-agent.ps1", "bash_completion.d/pf-agent"],
            "cache_logs": cache_logs,
            "user_data": user_data if remove_user_data else [],
        }
        retained = [] if remove_user_data else user_data
        return UninstallPlan(actions=actions, retained_paths=retained, remove_user_data=remove_user_data)


__all__ = ["UninstallPlan", "UninstallPlanner", "UninstallResult"]
