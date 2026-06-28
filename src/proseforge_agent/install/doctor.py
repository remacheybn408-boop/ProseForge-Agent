"""Read-only installation diagnostics."""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .app_dirs import AppDirs


@dataclass(frozen=True)
class DoctorCheck:
    """One diagnostic check result."""

    name: str
    section: str
    status: str
    detail: str
    recovery: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    """Collection of doctor checks."""

    checks: list[DoctorCheck]

    @property
    def status(self) -> str:
        if any(check.status == "fail" for check in self.checks):
            return "fail"
        if any(check.status == "warn" for check in self.checks):
            return "warn"
        return "ok"

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": [asdict(check) for check in self.checks]}

    def render_markdown(self) -> str:
        lines = ["# Installation Doctor", "", f"status: {self.status}", ""]
        for check in self.checks:
            detail = _redact(str(check.detail))
            lines.append(f"- [{check.status}] {check.section}.{check.name}: {detail}")
            if check.recovery:
                lines.append(f"  recovery: {check.recovery}")
        return "\n".join(lines) + "\n"


class InstallationDoctor:
    """Run read-only local environment checks."""

    def __init__(self, env: dict[str, str] | None = None, config: dict[str, Any] | None = None) -> None:
        self.env = dict(os.environ if env is None else env)
        self.config = dict(config or {})

    def run(self, section: str | None = None) -> DoctorReport:
        checks = [
            self._os_check(),
            self._python_check(),
            self._package_check(),
            self._config_check(),
            self._workspace_check(),
            self._proseforge_root_check(),
            self._provider_key_check(),
            self._secret_backend_check(),
            self._encoding_check(),
            self._paths_check(),
        ]
        if section:
            checks = [check for check in checks if check.section == section]
        return DoctorReport(checks=checks)

    def _os_check(self) -> DoctorCheck:
        return DoctorCheck("os", "platform", "ok", self.env.get("OS") or platform.system() or "unknown")

    def _python_check(self) -> DoctorCheck:
        version = self.env.get("PYTHON_VERSION") or ".".join(map(str, sys.version_info[:3]))
        major_minor = tuple(int(part) for part in version.split(".")[:2])
        ok = major_minor >= (3, 10)
        return DoctorCheck(
            "python_version",
            "python",
            "ok" if ok else "fail",
            version,
            None if ok else "Install Python 3.10 or newer",
        )

    def _package_check(self) -> DoctorCheck:
        installed = self.env.get("PACKAGE_INSTALLED", "1") != "0"
        return DoctorCheck(
            "package",
            "packaging",
            "ok" if installed else "fail",
            "pf-agent importable" if installed else "package metadata missing",
            None if installed else "python -m pip install -e .",
        )

    def _config_check(self) -> DoctorCheck:
        exists = self.env.get("CONFIG_EXISTS", "1") != "0" or Path(".pf-agent/config.yaml").exists()
        return DoctorCheck(
            "config",
            "config",
            "ok" if exists else "fail",
            "config present" if exists else "config missing",
            None if exists else "pf-agent init --portable --non-interactive",
        )

    def _workspace_check(self) -> DoctorCheck:
        writable = self.env.get("WORKSPACE_WRITABLE", "1") != "0"
        return DoctorCheck(
            "workspace",
            "workspace",
            "ok" if writable else "fail",
            "workspace writable" if writable else "workspace not writable",
            None if writable else "Choose a writable workspace directory",
        )

    def _proseforge_root_check(self) -> DoctorCheck:
        root = self.env.get("PROSEFORGE_ROOT") or self.config.get("proseforge_root")
        ok = bool(root)
        return DoctorCheck(
            "proseforge_root",
            "proseforge",
            "ok" if ok else "fail",
            "ProseForge root configured" if ok else "PROSEFORGE_ROOT missing",
            None if ok else "Set PROSEFORGE_ROOT or run pf-agent init",
        )

    def _provider_key_check(self) -> DoctorCheck:
        keys = [name for name in self.env if name.endswith("_API_KEY")]
        return DoctorCheck(
            "provider_keys",
            "providers",
            "ok" if keys else "warn",
            f"{len(keys)} provider key(s) configured",
            None if keys else "Run pf-agent provider setup --provider <name>",
        )

    def _secret_backend_check(self) -> DoctorCheck:
        backend = self.env.get("SECRET_BACKEND", "env")
        native = backend in {"credential_manager", "keychain", "secret_service"}
        return DoctorCheck(
            "secret_backend",
            "secrets",
            "ok" if native else "warn",
            f"backend={backend}",
            None if native else "Use native secret storage when available",
        )

    def _encoding_check(self) -> DoctorCheck:
        utf8 = self.env.get("PYTHONUTF8") == "1" or sys.getdefaultencoding().lower() == "utf-8"
        return DoctorCheck(
            "encoding",
            "encoding",
            "ok" if utf8 else "warn",
            "UTF-8 enabled" if utf8 else "terminal may not support UTF-8",
            None if utf8 else "Enable UTF-8 mode for your shell",
        )

    def _paths_check(self) -> DoctorCheck:
        current = (self.env.get("PF_TEST_PLATFORM") or platform.system() or "linux").lower()
        normalized = "windows" if current.startswith("win") else "macos" if current == "darwin" else current
        try:
            dirs = AppDirs.for_platform(normalized, self.env, portable=self.env.get("PF_PORTABLE") == "1")
        except Exception as exc:  # noqa: BLE001 - doctor reports recovery instead of raising
            return DoctorCheck("app_dirs", "paths", "fail", str(exc), "Set HOME or platform app-dir variables")
        return DoctorCheck("app_dirs", "paths", "ok", f"config={dirs.config_dir}")


def _redact(text: str) -> str:
    for key in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"):
        marker = key.lower()
        if marker in text.lower():
            return "[redacted]"
    return text.replace("sk-secret", "[redacted]")


__all__ = ["DoctorCheck", "DoctorReport", "InstallationDoctor"]
