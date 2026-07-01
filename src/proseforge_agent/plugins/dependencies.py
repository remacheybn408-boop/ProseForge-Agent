"""Dependency checks for local plugins."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Mapping

from ..errors import ConfigurationError
from .manifest import PluginManifest


@dataclass(frozen=True)
class PluginDependencyIssue:
    kind: str
    dependency: str
    message: str
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PluginDependencyReport:
    plugin_id: str
    status: str
    dependencies: list[str]
    issues: list[PluginDependencyIssue]
    install_commands: list[str]
    isolated_venv_supported: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["issues"] = [issue.to_dict() for issue in self.issues]
        return data


class PluginDependencyManager:
    """Validate plugin dependency declarations without installing them."""

    def __init__(self, root: str | Path, installed_versions: Mapping[str, str] | None = None) -> None:
        self.root = Path(root)
        self.plugins_dir = self.root / "plugins"
        self.installed_versions = {
            self._normalize_name(name): version for name, version in (installed_versions or {}).items()
        }

    def check(self, plugin_id_or_path: str | Path) -> PluginDependencyReport:
        manifest = self._load_manifest(plugin_id_or_path)
        dependencies = manifest.dependencies.get("python", [])
        issues: list[PluginDependencyIssue] = []
        install_commands = [f"pip install '{dependency}'" for dependency in dependencies]
        for dependency in dependencies:
            name, operator, expected = self._parse_requirement(dependency)
            installed = self._installed_version(name)
            if installed is None:
                issues.append(
                    PluginDependencyIssue(
                        kind="missing",
                        dependency=dependency,
                        message=f"{name} is not installed",
                        recommendation=f"Run dry-run plan first, then install with: pip install '{dependency}'",
                    )
                )
                continue
            if operator and expected and not self._satisfies(installed, operator, expected):
                issues.append(
                    PluginDependencyIssue(
                        kind="version_conflict",
                        dependency=dependency,
                        message=f"{name} {installed} does not satisfy {operator}{expected}",
                        recommendation=f"Use an isolated plugin environment or install: pip install '{dependency}'",
                    )
                )
        status = "ok" if not issues else "blocked"
        return PluginDependencyReport(
            plugin_id=manifest.id,
            status=status,
            dependencies=dependencies,
            issues=issues,
            install_commands=install_commands,
        )

    def _load_manifest(self, plugin_id_or_path: str | Path) -> PluginManifest:
        candidate = Path(plugin_id_or_path)
        if (candidate / "plugin.yaml").exists():
            return PluginManifest.load(candidate / "plugin.yaml")
        installed_manifest = self.plugins_dir / str(plugin_id_or_path) / "plugin.yaml"
        if installed_manifest.exists():
            return PluginManifest.load(installed_manifest)
        raise ConfigurationError(f"plugin manifest not found: {plugin_id_or_path}")

    def _installed_version(self, name: str) -> str | None:
        normalized = self._normalize_name(name)
        if normalized in self.installed_versions:
            return self.installed_versions[normalized]
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None

    @staticmethod
    def _parse_requirement(requirement: str) -> tuple[str, str, str]:
        for operator in (">=", "==", "<=", ">", "<"):
            if operator in requirement:
                name, version = requirement.split(operator, 1)
                return name.strip(), operator, version.strip()
        return requirement.strip(), "", ""

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower().replace("_", "-")

    @classmethod
    def _satisfies(cls, installed: str, operator: str, expected: str) -> bool:
        left = cls._version_tuple(installed)
        right = cls._version_tuple(expected)
        if operator == "==":
            return left == right
        if operator == ">=":
            return left >= right
        if operator == "<=":
            return left <= right
        if operator == ">":
            return left > right
        if operator == "<":
            return left < right
        return True

    @staticmethod
    def _version_tuple(version: str) -> tuple[int | str, ...]:
        parts: list[int | str] = []
        for part in version.replace("-", ".").split("."):
            parts.append(int(part) if part.isdigit() else part)
        return tuple(parts)


__all__ = ["PluginDependencyIssue", "PluginDependencyManager", "PluginDependencyReport"]
