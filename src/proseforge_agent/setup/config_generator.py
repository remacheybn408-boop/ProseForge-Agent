"""Safe setup config generation and redaction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .modes import SetupMode


SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]+)", re.IGNORECASE)


class SetupConfigGenerator:
    """Generate setup config without writing raw API keys."""

    def build(
        self,
        *,
        mode: SetupMode,
        workspace_path: str | Path,
        providers: dict[str, dict[str, Any]],
        existing: dict[str, Any] | None = None,
        engine_enabled: bool = False,
    ) -> dict[str, Any]:
        config = dict(existing or {})
        config["setup"] = {
            **_mapping(config.get("setup")),
            "completed": True,
            "mode": mode.value,
        }
        config["workspace"] = {
            **_mapping(config.get("workspace")),
            "path": str(Path(workspace_path)),
        }
        merged_providers = _mapping(config.get("providers"))
        merged_providers.update(providers)
        config["providers"] = merged_providers
        config["default_provider"] = "fake" if mode == SetupMode.MINIMAL else _default_provider(merged_providers)
        config["engine"] = {
            **_mapping(config.get("engine")),
            "enabled": bool(engine_enabled),
        }
        return config

    def render(self, config: dict[str, Any]) -> str:
        return yaml.safe_dump(config, allow_unicode=True, sort_keys=True)


def load_existing(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def redact_config_text(text: str) -> str:
    redacted_lines: list[str] = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(token in lowered for token in ("api_key:", "token:", "password:", "secret:")):
            key = line.split(":", maxsplit=1)[0]
            redacted_lines.append(f"{key}: [redacted]")
            continue
        redacted_lines.append(SECRET_RE.sub("[redacted]", line))
    return "\n".join(redacted_lines) + ("\n" if text.endswith("\n") else "")


def provider_entry(
    name: str,
    *,
    configured: bool,
    key_ref: str | None = None,
    model: str | None = None,
    status: str = "ok",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "enabled": True,
        "configured": configured,
        "kind": "fake" if name == "fake" else "llm",
        "model": model or ("fake" if name == "fake" else f"{name}-chat"),
        "status": status,
    }
    if key_ref:
        payload["key_ref"] = key_ref
    return payload


def _default_provider(providers: dict[str, dict[str, Any]]) -> str:
    for name, payload in providers.items():
        if name != "fake" and payload.get("enabled") and payload.get("configured"):
            return name
    return "fake"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


__all__ = [
    "SetupConfigGenerator",
    "load_existing",
    "provider_entry",
    "redact_config_text",
]
