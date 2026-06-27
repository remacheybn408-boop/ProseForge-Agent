"""Extension registry: compatibility, isolation, and discovery.

The registry registers extensions only when they are compatible with the
running agent version and declare known extension points. A failing extension is
disabled and its error recorded rather than propagated, so one broken plug-in
never crashes an unrelated command. Extensions can be discovered by loading a
module that exposes a top-level ``EXTENSION`` instance.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from .base import EXTENSION_POINTS, Extension, ExtensionError, version_satisfies


class ExtensionRegistry:
    """Register, query, and safely invoke extensions for one agent version."""

    def __init__(self, agent_version: str) -> None:
        self._agent_version = agent_version
        self._by_id: dict[str, Extension] = {}
        self._errors: list[dict] = []

    def register(self, extension: Extension) -> Extension:
        for capability in extension.capabilities:
            if capability not in EXTENSION_POINTS:
                raise ExtensionError(
                    f"extension {extension.id!r} declares unknown extension point "
                    f"{capability!r}; known points: {EXTENSION_POINTS}"
                )
        if not version_satisfies(self._agent_version, extension.compatible_agent_range):
            raise ExtensionError(
                f"extension {extension.id!r} is not compatible with agent "
                f"{self._agent_version} (requires {extension.compatible_agent_range})"
            )
        if extension.id in self._by_id:
            raise ExtensionError(f"duplicate extension id {extension.id!r}")
        self._by_id[extension.id] = extension
        return extension

    def get(self, extension_id: str) -> Extension | None:
        return self._by_id.get(extension_id)

    def list_ids(self) -> list[str]:
        return sorted(self._by_id)

    def enabled_extensions(self, point: str | None = None) -> list[Extension]:
        result = []
        for extension in self._by_id.values():
            if not extension.enabled:
                continue
            if point is not None and point not in extension.capabilities:
                continue
            result.append(extension)
        return result

    def disable(self, extension_id: str, *, reason: str) -> None:
        extension = self._by_id.get(extension_id)
        if extension is None:
            raise ExtensionError(f"unknown extension {extension_id!r}")
        extension.enabled = False
        self._errors.append({"id": extension_id, "reason": reason})

    def safe_invoke(self, extension: Extension, method: str, *args, **kwargs):
        """Invoke an extension method, isolating any failure.

        A disabled extension yields ``None``. Any exception disables the
        extension and records the error instead of propagating, so unrelated
        extensions and commands keep working.
        """
        if not extension.enabled:
            return None
        try:
            return getattr(extension, method)(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - isolation is the whole point
            self.disable(extension.id, reason=f"{method} failed: {exc}")
            return None

    def errors(self) -> list[dict]:
        return list(self._errors)

    def load_module(self, path: str | Path) -> Extension:
        """Load an extension from a module file exposing ``EXTENSION``."""
        path = Path(path)
        spec = importlib.util.spec_from_file_location(f"pf_ext_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ExtensionError(f"cannot load extension module at {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        extension = getattr(module, "EXTENSION", None)
        if not isinstance(extension, Extension):
            raise ExtensionError(
                f"extension module {path} must define a top-level EXTENSION instance"
            )
        return extension


__all__ = ["ExtensionRegistry"]
