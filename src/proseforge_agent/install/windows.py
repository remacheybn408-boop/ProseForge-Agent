"""Windows-specific native runtime checks."""

from __future__ import annotations

import os

from .app_dirs import AppDirs
from .doctor import DoctorCheck
from .platform_io import TerminalCaps
from .secrets import SecretStore


class WindowsChecks:
    """Read-only Windows native support diagnostics."""

    def __init__(self, env: dict[str, str] | None = None) -> None:
        # Hermetic like InstallationDoctor: when a caller supplies an env it is
        # authoritative, so machine variables (e.g. WT_SESSION inside Windows
        # Terminal) can't leak in and flip a check's result.
        self.env = dict(os.environ if env is None else env)

    def run(self) -> list[DoctorCheck]:
        return [
            self._powershell_utf8(),
            self._credential_manager(),
            self._long_paths(),
            self._spaces_in_paths(),
        ]

    def _powershell_utf8(self) -> DoctorCheck:
        caps = TerminalCaps.detect(self.env)
        ok = caps.supports_utf8
        return DoctorCheck(
            "powershell_utf8",
            "windows",
            "ok" if ok else "warn",
            "UTF-8 terminal" if ok else "ASCII fallback active for bare CMD",
            None if ok else "Use Windows Terminal or set PYTHONUTF8=1",
        )

    def _credential_manager(self) -> DoctorCheck:
        available = self.env.get("CREDENTIAL_MANAGER", "1") != "0"
        store = SecretStore.for_platform("windows", available)
        return DoctorCheck(
            "credential_manager",
            "windows",
            "ok" if store.protected else "warn",
            f"backend={store.backend}",
            None if store.protected else "Use environment fallback or enable Credential Manager",
        )

    def _long_paths(self) -> DoctorCheck:
        enabled = self.env.get("LONG_PATHS_ENABLED", "1") != "0"
        return DoctorCheck(
            "long_paths",
            "windows",
            "ok" if enabled else "warn",
            "long paths enabled" if enabled else "long paths disabled",
            None if enabled else "Set HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem\\LongPathsEnabled=1",
        )

    def _spaces_in_paths(self) -> DoctorCheck:
        try:
            dirs = AppDirs.for_platform("windows", self.env)
        except Exception as exc:  # noqa: BLE001 - keep diagnostics non-throwing
            return DoctorCheck(
                "spaces_in_paths",
                "windows",
                "warn",
                str(exc),
                "Set APPDATA and LOCALAPPDATA",
            )
        return DoctorCheck(
            "spaces_in_paths",
            "windows",
            "ok",
            f"config={dirs.config_dir}",
        )


__all__ = ["WindowsChecks"]
