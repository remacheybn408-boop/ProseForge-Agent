"""OS installer builder and signing (Task 185).

The builder derives the per-platform installer recipe from the Task 184 binary
payload and runs the real packaging/signing commands through an injectable
runner. Signing is credential-gated: when the credential is absent, the sign
step is warn-skipped so an unsigned-but-valid installer is still produced.

Credentials never appear in the recipe, the report, or any log line. Callers
that need to inject a certificate reference should use ``credential_reader``
so the resolved value stays inside the runner call and is redacted for output.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from ..errors import ConfigurationError
from .app_dirs import AppDirs


_PLATFORMS = ("windows", "macos", "linux")


class _Runner(Protocol):
    def run(self, argv: list[str], *, env: dict[str, str] | None = None) -> int: ...


@dataclass(frozen=True)
class InstallerRecipe:
    """Ordered argv for the per-platform installer build."""

    platform: str
    artifact_name: str
    install_dir: str
    package_command: list[str]
    sign_command: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallerReport:
    """Outcome of an installer build with portable, redacted details."""

    passed: bool
    artifact_name: str
    signed: bool
    steps: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class InstallerBuilder:
    """Package and sign the Task 184 binary into a per-OS installer."""

    def __init__(
        self,
        platform: str,
        app_dirs: AppDirs,
        runner: _Runner,
        *,
        credential_reader: Callable[[str], str | None] | None = None,
    ) -> None:
        if platform not in _PLATFORMS:
            raise ConfigurationError(
                f"unknown installer platform {platform!r}; expected one of {_PLATFORMS}"
            )
        self.platform = platform
        self.app_dirs = app_dirs
        self._runner = runner
        self._credential_reader = credential_reader or (lambda _name: None)

    def recipe(self) -> InstallerRecipe:
        install_dir = str(self.app_dirs.data_dir).replace("\\", "/")
        if self.platform == "windows":
            artifact = "pf-agent-windows.msi"
            package = [
                "candle",
                "-arch",
                "x64",
                "-o",
                f"build/{artifact.replace('.msi', '.wixobj')}",
                "build/pf-agent.wxs",
            ]
            sign = [
                "signtool",
                "sign",
                "/fd",
                "SHA256",
                "/tr",
                "http://timestamp.digicert.com",
                "/td",
                "SHA256",
                f"dist/{artifact}",
            ]
        elif self.platform == "macos":
            artifact = "pf-agent-macos.dmg"
            package = [
                "hdiutil",
                "create",
                "-volname",
                "ProseForge Agent",
                "-srcfolder",
                "dist/pf-agent.app",
                "-ov",
                "-format",
                "UDZO",
                f"dist/{artifact}",
            ]
            sign = [
                "codesign",
                "--force",
                "--options",
                "runtime",
                "--timestamp",
                f"dist/{artifact}",
            ]
        else:  # linux
            artifact = "install.sh"
            package = [
                "sh",
                "-c",
                "cat scripts/install-header.sh dist/pf-agent-linux-x64 > dist/install.sh && chmod +x dist/install.sh",
            ]
            sign = [
                "gpg",
                "--detach-sign",
                "--armor",
                "--output",
                f"dist/{artifact}.asc",
                f"dist/{artifact}",
            ]
        return InstallerRecipe(
            platform=self.platform,
            artifact_name=artifact,
            install_dir=install_dir,
            package_command=package,
            sign_command=sign,
        )

    def build(self, *, sign: bool = True, dry_run: bool = False) -> InstallerReport:
        recipe = self.recipe()
        steps: list[str] = []
        skipped: list[str] = []

        if dry_run:
            steps.append(f"package: dry_run -> {' '.join(recipe.package_command)}")
            if sign:
                steps.append(f"sign: dry_run -> {' '.join(recipe.sign_command)}")
            summary = f"dry_run installer plan for {recipe.artifact_name}"
            return InstallerReport(
                passed=True,
                artifact_name=recipe.artifact_name,
                signed=False,
                steps=steps,
                skipped=skipped,
                summary=summary,
            )

        package_exit = self._runner.run(recipe.package_command)
        steps.append(f"package: exit={package_exit}")
        if package_exit != 0:
            return InstallerReport(
                passed=False,
                artifact_name=recipe.artifact_name,
                signed=False,
                steps=steps,
                skipped=skipped,
                summary=f"package failed with exit code {package_exit}",
            )

        signed = False
        if sign:
            credential = self._credential_reader(self._credential_key())
            if not credential:
                skipped.append(f"sign: skipped (no {self._credential_key()} credential available)")
            else:
                sign_exit = self._runner.run(
                    recipe.sign_command,
                    env={self._credential_key(): credential},
                )
                steps.append(f"sign: exit={sign_exit}")
                if sign_exit != 0:
                    skipped.append(f"sign: skipped (signer exited {sign_exit})")
                else:
                    signed = True

        if signed:
            summary = f"built and signed {recipe.artifact_name}"
        elif sign:
            summary = f"built {recipe.artifact_name} unsigned (warning: signing skipped)"
        else:
            summary = f"built {recipe.artifact_name} unsigned"
        return InstallerReport(
            passed=True,
            artifact_name=recipe.artifact_name,
            signed=signed,
            steps=steps,
            skipped=skipped,
            summary=summary,
        )

    def _credential_key(self) -> str:
        return {
            "windows": "WINDOWS_SIGNING_CERT",
            "macos": "APPLE_TEAM_ID",
            "linux": "GPG_KEY_ID",
        }[self.platform]


__all__ = ["InstallerBuilder", "InstallerRecipe", "InstallerReport"]
