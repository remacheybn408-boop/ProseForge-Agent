"""Linux-specific native runtime checks."""

from __future__ import annotations

import os

from .app_dirs import AppDirs
from .doctor import DoctorCheck
from .platform_io import TerminalCaps
from .secrets import SecretStore


class LinuxChecks:
    """Read-only Linux native support diagnostics."""

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self.env = dict(os.environ)
        self.env.update(env or {})

    def run(self) -> list[DoctorCheck]:
        return [
            self._xdg_dirs(),
            self._secret_service(),
            self._terminal_utf8(),
            self._systemd_user_service(),
        ]

    def _xdg_dirs(self) -> DoctorCheck:
        try:
            dirs = AppDirs.for_platform("linux", self.env)
        except Exception as exc:  # noqa: BLE001
            return DoctorCheck("xdg_dirs", "linux", "fail", str(exc), "Set HOME or XDG_* directories")
        return DoctorCheck("xdg_dirs", "linux", "ok", f"config={str(dirs.config_dir).replace(chr(92), '/')}")

    def _secret_service(self) -> DoctorCheck:
        available = self.env.get("SECRET_SERVICE", "1") != "0"
        store = SecretStore.for_platform("linux", available)
        return DoctorCheck(
            "secret_service",
            "linux",
            "ok" if store.protected else "warn",
            f"backend={store.backend}",
            None if store.protected else "Install Secret Service or use env_fallback",
        )

    def _terminal_utf8(self) -> DoctorCheck:
        env = dict(self.env)
        if "UTF-8" in env.get("LANG", "").upper():
            env["PYTHONUTF8"] = "1"
        caps = TerminalCaps.detect(env)
        return DoctorCheck(
            "terminal_utf8",
            "linux",
            "ok" if caps.supports_utf8 else "warn",
            "UTF-8 terminal" if caps.supports_utf8 else "terminal may need UTF-8 locale",
            None if caps.supports_utf8 else "Set LANG to a UTF-8 locale",
        )

    def _systemd_user_service(self) -> DoctorCheck:
        available = self.env.get("SYSTEMD_USER", "1") != "0"
        return DoctorCheck(
            "systemd_user_service",
            "linux",
            "ok" if available else "warn",
            "systemd --user available" if available else "manual service setup required",
            None if available else "Run systemctl --user daemon-reload after installing service files",
        )


__all__ = ["LinuxChecks"]
