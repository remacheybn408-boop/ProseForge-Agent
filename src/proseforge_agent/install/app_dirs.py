"""Cross-platform application directory resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError


@dataclass(frozen=True)
class AppDirs:
    """Resolved config, data, cache, and log directories."""

    config_dir: Path
    data_dir: Path
    cache_dir: Path
    log_dir: Path
    platform: str
    portable: bool = False

    @classmethod
    def for_platform(
        cls,
        platform: str,
        env: dict[str, str],
        portable: bool = False,
    ) -> "AppDirs":
        normalized = platform.lower()
        if portable:
            root = Path(env.get("PROSEFORGE_AGENT_WORKSPACE", ".pf-agent"))
            return cls(
                config_dir=root / "config",
                data_dir=root / "data",
                cache_dir=root / "cache",
                log_dir=root / "logs",
                platform=normalized,
                portable=True,
            )
        if normalized in {"windows", "win32"}:
            return cls._windows(env)
        if normalized in {"macos", "darwin"}:
            return cls._macos(env)
        if normalized == "linux":
            return cls._linux(env)
        raise ConfigurationError(f"unknown platform {platform!r}")

    @classmethod
    def _windows(cls, env: dict[str, str]) -> "AppDirs":
        roaming = _required(env, "APPDATA", fallback=env.get("HOME") or env.get("USERPROFILE"))
        local = _required(env, "LOCALAPPDATA", fallback=env.get("HOME") or env.get("USERPROFILE"))
        name = "ProseForge Agent"
        return cls(
            config_dir=Path(roaming) / name,
            data_dir=Path(local) / name,
            cache_dir=Path(local) / name / "Cache",
            log_dir=Path(local) / name / "Logs",
            platform="windows",
        )

    @classmethod
    def _macos(cls, env: dict[str, str]) -> "AppDirs":
        home = Path(_required(env, "HOME"))
        name = "ProseForge Agent"
        return cls(
            config_dir=home / "Library" / "Application Support" / name,
            data_dir=home / "Library" / "Application Support" / name,
            cache_dir=home / "Library" / "Caches" / name,
            log_dir=home / "Library" / "Logs" / name,
            platform="macos",
        )

    @classmethod
    def _linux(cls, env: dict[str, str]) -> "AppDirs":
        home = Path(_required(env, "HOME"))
        name = "proseforge-agent"
        config = Path(env.get("XDG_CONFIG_HOME") or home / ".config") / name
        data = Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / name
        cache = Path(env.get("XDG_CACHE_HOME") or home / ".cache") / name
        state = Path(env.get("XDG_STATE_HOME") or home / ".local" / "state") / name
        return cls(
            config_dir=config,
            data_dir=data,
            cache_dir=cache,
            log_dir=state / "logs",
            platform="linux",
        )


def _required(env: dict[str, str], key: str, fallback: str | None = None) -> str:
    value = env.get(key) or fallback
    if not value:
        raise ConfigurationError(f"required environment value {key!r} is missing")
    return value


__all__ = ["AppDirs"]
