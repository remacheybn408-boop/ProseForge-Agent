"""Managed install planner (Task 187).

Produces the exact, ordered argv the ``scripts/install.sh`` and
``scripts/install.ps1`` bootstrap scripts execute, so tests can assert phase
order and command shape without running a shell. ``uv`` is preferred with a
``pipx`` fallback; installing inside an active virtualenv is refused unless
explicitly allowed.

The planner is pure: ``.plan()`` reads only its constructor inputs and writes
nothing to disk.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


_PACKAGE = "proseforge-agent"
_PHASE_ORDER = (
    "preflight",
    "ensure_python",
    "ensure_manager",
    "install_package",
    "register_path",
    "post_verify",
)


@dataclass(frozen=True)
class InstallPhase:
    """One ordered step of the managed install."""

    name: str
    command: list[str]
    optional: bool = False
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallPlan:
    """Ordered install phases, or a refusal with a reason."""

    os_name: str
    arch: str
    package: str
    phases: list[InstallPhase] = field(default_factory=list)
    refused: bool = False
    refusal_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "os_name": self.os_name,
            "arch": self.arch,
            "package": self.package,
            "refused": self.refused,
            "refusal_reason": self.refusal_reason,
            "phases": [phase.to_dict() for phase in self.phases],
        }


class ManagedInstallPlanner:
    """Compute the ordered install plan for one OS/arch/environment."""

    def __init__(self, os_name: str, arch: str, existing: dict[str, bool] | None = None) -> None:
        self.os_name = os_name.lower()
        self.arch = arch
        self.existing = dict(existing or {})

    def _is_windows(self) -> bool:
        return self.os_name in {"windows", "win32", "win"}

    def plan(
        self,
        package: str = _PACKAGE,
        *,
        ref: str | None = None,
        system: bool = False,
        allow_venv: bool = False,
    ) -> InstallPlan:
        if self.existing.get("active_venv") and not allow_venv:
            return InstallPlan(
                os_name=self.os_name,
                arch=self.arch,
                package=package,
                refused=True,
                refusal_reason=(
                    "refusing to install inside an active virtualenv; "
                    "deactivate it or re-run with --allow-venv"
                ),
            )

        phases = [
            self._preflight(system=system),
            self._ensure_python(),
            self._ensure_manager(),
            self._install_package(package, ref=ref),
            self._register_path(),
            self._post_verify(),
        ]
        return InstallPlan(os_name=self.os_name, arch=self.arch, package=package, phases=phases)

    # -- phases ----------------------------------------------------------

    def _preflight(self, *, system: bool) -> InstallPhase:
        scope = "system" if system else "user"
        return InstallPhase(
            name="preflight",
            command=["pf-agent-install", "--preflight", f"--scope={scope}"],
            remediation="ensure you are not root (unless --system) and pf-agent is not already installed",
        )

    def _ensure_python(self) -> InstallPhase:
        if self.existing.get("python311"):
            return InstallPhase(
                name="ensure_python",
                command=["python", "--version"],
                optional=True,
                remediation="Python 3.10+ already present",
            )
        if self._is_windows():
            command = ["winget", "install", "--id", "Python.Python.3.11", "-e"]
            remediation = "install Python 3.11 from python.org if winget is unavailable"
        else:
            command = ["uv", "python", "install", "3.11"]
            remediation = "install Python 3.11 via your package manager if uv cannot"
        return InstallPhase(name="ensure_python", command=command, remediation=remediation)

    def _ensure_manager(self) -> InstallPhase:
        if self.existing.get("uv"):
            return InstallPhase(
                name="ensure_manager",
                command=["uv", "--version"],
                optional=True,
                remediation="uv already present",
            )
        if self.existing.get("pipx"):
            return InstallPhase(
                name="ensure_manager",
                command=["pipx", "--version"],
                optional=True,
                remediation="pipx already present (uv preferred but not required)",
            )
        if self._is_windows():
            command = ["powershell", "-c", "irm https://astral.sh/uv/install.ps1 | iex"]
        else:
            command = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
        return InstallPhase(
            name="ensure_manager",
            command=command,
            remediation="install uv manually from https://astral.sh/uv if the bootstrap fails",
        )

    def _install_package(self, package: str, *, ref: str | None) -> InstallPhase:
        target = f"git+https://github.com/NousResearch/proseforge-agent@{ref}" if ref else package
        if self.existing.get("uv") or not self.existing.get("pipx"):
            command = ["uv", "tool", "install", target]
        else:
            command = ["pipx", "install", target]
        return InstallPhase(
            name="install_package",
            command=command,
            remediation="verify network access and that the package/ref exists",
        )

    def _register_path(self) -> InstallPhase:
        if self._is_windows():
            command = [
                "setx",
                "PATH",
                "%LOCALAPPDATA%\\Programs\\ProseForge Agent;%PATH%",
            ]
            remediation = "add %LOCALAPPDATA%\\Programs\\ProseForge Agent to PATH manually"
        else:
            command = [
                "sh",
                "-c",
                'printf "export PATH=\\"$HOME/.local/bin:$PATH\\"\\n" >> "$HOME/.profile"',
            ]
            remediation = "add $HOME/.local/bin to your shell PATH manually"
        return InstallPhase(name="register_path", command=command, remediation=remediation)

    def _post_verify(self) -> InstallPhase:
        return InstallPhase(
            name="post_verify",
            command=["pf-agent", "doctor", "--format", "json"],
            remediation="if doctor fails, re-run the installer or open an issue",
        )


__all__ = ["InstallPhase", "InstallPlan", "ManagedInstallPlanner"]
