"""Load and validate the portable ProseForge Agent configuration.

Configuration is the portability boundary of the whole tool: the ProseForge
engine root and the Agent workspace root are supplied through environment
variables or the config file, never baked into a machine-specific path.

The config file is nested::

    paths:
      proseforge_root: ${PROSEFORGE_ROOT}
      workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
    project:
      slug: demo
      title: Demo

``${VAR}`` and ``${VAR:-default}`` are expanded from the environment. Relative
paths resolve from the directory that contains the config file, so the same
file is portable across machines and operating systems.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import ConfigurationError

# ${VAR} or ${VAR:-default}
_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


@dataclass(frozen=True)
class ProjectConfig:
    """Identity of the novel project this config drives."""

    slug: str
    title: str


@dataclass(frozen=True)
class AgentConfig:
    """Resolved, validated agent configuration.

    Paths are already environment-expanded and resolved to absolute paths
    relative to the config file directory.
    """

    proseforge_root: Path
    workspace_root: Path
    project: ProjectConfig


def _expand(value: str, *, key: str) -> str:
    """Expand ``${VAR}`` / ``${VAR:-default}`` references against the environment.

    Raises :class:`ConfigurationError` (naming ``key``) when a referenced
    variable is unset and no default was supplied.
    """

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        raise ConfigurationError(
            f"{key}: environment variable {name!r} is not set and has no default"
        )

    return _VAR_PATTERN.sub(replace, value)


def _require(data: dict, section: str, field: str) -> object:
    """Return ``data[field]`` or raise a ``ConfigurationError`` naming the key path."""
    if not isinstance(data, dict) or field not in data or data[field] in (None, ""):
        raise ConfigurationError(f"{section}.{field} is required")
    return data[field]


def _resolve_path(raw: object, *, base: Path, key: str) -> Path:
    """Expand environment references in ``raw`` and resolve relative to ``base``."""
    if not isinstance(raw, str):
        raise ConfigurationError(f"{key} must be a string path")
    expanded = _expand(raw, key=key)
    candidate = Path(expanded)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def load_agent_config(path: str | os.PathLike[str]) -> AgentConfig:
    """Load, expand, and validate the agent config at ``path``.

    Relative paths in the config resolve from the config file's own directory.
    """
    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"cannot read config file {config_path}: {exc}") from exc

    loaded = yaml.safe_load(text)
    if loaded is None:
        raise ConfigurationError(f"config file {config_path} is empty")
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"config file {config_path} must be a mapping")

    base = config_path.parent

    paths = loaded.get("paths")
    if not isinstance(paths, dict):
        raise ConfigurationError("paths section is required")
    proseforge_root_raw = _require(paths, "paths", "proseforge_root")
    workspace_root_raw = _require(paths, "paths", "workspace_root")

    project = loaded.get("project")
    if not isinstance(project, dict):
        raise ConfigurationError("project section is required")
    slug = _require(project, "project", "slug")
    title = _require(project, "project", "title")

    return AgentConfig(
        proseforge_root=_resolve_path(
            proseforge_root_raw, base=base, key="paths.proseforge_root"
        ),
        workspace_root=_resolve_path(
            workspace_root_raw, base=base, key="paths.workspace_root"
        ),
        project=ProjectConfig(slug=str(slug), title=str(title)),
    )


__all__ = ["AgentConfig", "ProjectConfig", "load_agent_config"]
