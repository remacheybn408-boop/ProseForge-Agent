"""Stdlib-only ``.env`` loader (Task 191).

No third-party dependency. Populates ``os.environ`` with keys not already set,
so users can drop secrets into a familiar ``.env`` file instead of exporting
shell variables. Load precedence (higher wins):

1. existing ``os.environ`` (never overridden by default)
2. ``.env.local``
3. ``.env``
4. ``<config_dir>/proseforge-agent.env`` (machine defaults)

``DotenvLoader`` takes an ordered list of paths from LOWEST to HIGHEST
precedence and merges them; ``load_default_files`` builds that list.
"""

from __future__ import annotations

import os
from pathlib import Path

from .errors import ConfigurationError


# Environment keys the application recognizes; every key must be documented in
# `.env.example` (enforced by test_env_example_exists_and_covers_recognized_keys).
RECOGNIZED_KEYS = (
    "PROSEFORGE_ROOT",
    "PROSEFORGE_AGENT_WORKSPACE",
    "PF_AGENT_SKIP_FIRST_RUN",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "QWEN_API_KEY",
    "TWINE_USERNAME",
    "TWINE_PASSWORD",
    "PYTHONUTF8",
    "PYTHONIOENCODING",
)

_MACHINE_ENV_NAME = "proseforge-agent.env"


def _valid_key(key: str) -> bool:
    return bool(key) and all(ch.isalnum() or ch == "_" for ch in key) and not key[0].isdigit()


class DotenvLoader:
    """Parse and merge ``.env`` files into ``os.environ``."""

    def __init__(self, paths: list[Path]) -> None:
        self.paths = [Path(p) for p in paths]
        self.warnings: list[str] = []

    def parse_one(self, path: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        path = Path(path)
        if not path.exists():
            return result
        raw = path.read_text(encoding="utf-8")
        if "\x00" in raw:
            raise ConfigurationError(f".env file {path} contains NUL bytes")
        for lineno, line in enumerate(raw.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                self.warnings.append(f"{path}:{lineno}: ignored line with no '=': {stripped!r}")
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export ") :].strip()
            if not _valid_key(key):
                self.warnings.append(f"{path}:{lineno}: ignored invalid key {key!r}")
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            result[key] = value
        return result

    def load(self, *, override: bool = False) -> dict[str, str]:
        resolved: dict[str, str] = {}
        source: dict[str, str] = {}
        # paths are ordered low-to-high precedence; later files win.
        for path in self.paths:
            for key, value in self.parse_one(path).items():
                resolved[key] = value
                source[key] = str(path)

        audit: dict[str, str] = {}
        for key, value in resolved.items():
            if override or key not in os.environ:
                os.environ[key] = value
                audit[key] = source[key]
        return audit


def default_files(root: str | Path = ".", config_dir: str | Path | None = None) -> list[Path]:
    """Ordered low-to-high precedence file list for the default load."""
    root_path = Path(root)
    files: list[Path] = []
    if config_dir is not None:
        files.append(Path(config_dir) / _MACHINE_ENV_NAME)
    files.append(root_path / ".env")
    files.append(root_path / ".env.local")
    return files


def load_default_files(
    *,
    root: str | Path = ".",
    config_dir: str | Path | None = None,
    override: bool = False,
) -> dict[str, str]:
    """Resolve and load the standard ``.env`` file set. Never raises on I/O."""
    try:
        return DotenvLoader(default_files(root=root, config_dir=config_dir)).load(override=override)
    except ConfigurationError:
        raise
    except Exception:  # noqa: BLE001 - environment loading must not break startup
        return {}


__all__ = ["RECOGNIZED_KEYS", "DotenvLoader", "default_files", "load_default_files"]
