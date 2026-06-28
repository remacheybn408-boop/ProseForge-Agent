"""macOS-specific native runtime checks."""

from __future__ import annotations

import os

from .app_dirs import AppDirs
from .doctor import DoctorCheck
from .secrets import SecretStore


class MacOSChecks:
    """Read-only macOS native support diagnostics."""

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self.env = dict(os.environ)
        self.env.update(env or {})

    def run(self) -> list[DoctorCheck]:
        return [
            self._keychain(),
            self._application_support(),
            self._zsh_shell(),
            self._gatekeeper_note(),
        ]

    def _keychain(self) -> DoctorCheck:
        available = self.env.get("KEYCHAIN_AVAILABLE", "1") != "0"
        store = SecretStore.for_platform("macos", available)
        return DoctorCheck(
            "keychain",
            "macos",
            "ok" if store.protected else "warn",
            f"backend={store.backend}",
            None if store.protected else "Use env fallback or enable Keychain access",
        )

    def _application_support(self) -> DoctorCheck:
        try:
            dirs = AppDirs.for_platform("macos", self.env)
        except Exception as exc:  # noqa: BLE001
            return DoctorCheck("application_support", "macos", "fail", str(exc), "Set HOME")
        return DoctorCheck("application_support", "macos", "ok", f"config={str(dirs.config_dir).replace(chr(92), '/')}")

    def _zsh_shell(self) -> DoctorCheck:
        shell = self.env.get("SHELL", "")
        ok = shell.endswith("/zsh")
        return DoctorCheck(
            "zsh_shell",
            "macos",
            "ok" if ok else "warn",
            f"shell={shell or '(unknown)'}",
            None if ok else "Use zsh or install shell completions for your shell",
        )

    def _gatekeeper_note(self) -> DoctorCheck:
        return DoctorCheck(
            "gatekeeper_note",
            "macos",
            "warn",
            "manual Gatekeeper/notarization check required for packaged binaries",
            "Validate packaged app with spctl before release",
        )


__all__ = ["MacOSChecks"]
