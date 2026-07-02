"""Safe setup config generation and redaction."""

from __future__ import annotations

import re
from copy import deepcopy
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
        config = self.build_product_config(
            mode=mode,
            workspace_path=workspace_path,
            providers=providers,
            existing=existing,
            engine_enabled=engine_enabled,
        )
        llm = _mapping(config.get("llm"))
        paths = _mapping(config.get("paths"))
        # Compatibility aliases for pre-Task-78 setup consumers/tests.
        config["providers"] = deepcopy(_mapping(llm.get("providers")))
        config["default_provider"] = llm.get("default_provider", "fake")
        config["workspace"] = {
            **_mapping(config.get("workspace")),
            "path": paths.get("workspace_root", _workspace_text(workspace_path)),
        }
        config["engine"] = {
            **_mapping(config.get("engine")),
            "enabled": bool(engine_enabled),
        }
        return config

    def build_product_config(
        self,
        *,
        mode: SetupMode,
        workspace_path: str | Path,
        providers: dict[str, dict[str, Any]],
        existing: dict[str, Any] | None = None,
        engine_enabled: bool = False,
    ) -> dict[str, Any]:
        config = dict(existing or {})
        existing_llm = _mapping(config.get("llm"))
        existing_paths = _mapping(config.get("paths"))
        existing_agent = _mapping(config.get("agent"))
        existing_setup = _mapping(config.get("setup"))
        existing_provider_map = _mapping(existing_llm.get("providers")) or _mapping(config.get("providers"))
        provider_map = {
            name: _normalize_provider_payload(payload)
            for name, payload in existing_provider_map.items()
            if isinstance(payload, dict)
        }
        provider_map.update(
            {name: _normalize_provider_payload(payload) for name, payload in providers.items()}
        )
        config["setup"] = {
            **existing_setup,
            "completed": True,
            "mode": mode.value,
        }
        config["agent"] = {
            "profile": "default",
            "language": "zh-CN",
            "system_prompt_template": "professional_novel_editor",
            **existing_agent,
        }
        default_provider = "fake" if mode == SetupMode.MINIMAL else _default_provider(provider_map)
        config["llm"] = {
            **existing_llm,
            "default_provider": default_provider,
            "fallback_provider": "fake",
            "providers": provider_map,
        }
        config["paths"] = {
            **existing_paths,
            "workspace_root": _workspace_text(workspace_path),
        }
        config["engine"] = {
            **_mapping(config.get("engine")),
            "enabled": bool(engine_enabled),
        }
        return config

    def render(self, config: dict[str, Any]) -> str:
        return yaml.safe_dump(config, allow_unicode=True, sort_keys=True)

    def render_env_template(self, providers: dict[str, dict[str, Any]]) -> str:
        keys = []
        for name in sorted(providers):
            if name == "fake":
                continue
            keys.append(f"{name.upper()}_API_KEY=")
        lines = ["# ProseForge Agent environment overrides. Do not commit real keys."]
        lines.extend(keys or ["# No external provider keys required."])
        return "\n".join(lines) + "\n"


def known_config_keys() -> tuple[str, ...]:
    """Dotted paths the product config recognizes.

    Used by `pf-agent init --config` and by the example-seed coverage test so
    the annotated `configs/pf-agent.example.yaml` cannot silently drift from the
    keys the generator actually produces.
    """
    return (
        "setup.completed",
        "setup.mode",
        "agent.profile",
        "agent.language",
        "agent.system_prompt_template",
        "llm.default_provider",
        "llm.fallback_provider",
        "llm.providers",
        "paths.workspace_root",
        "engine.enabled",
    )


def example_config_text() -> str:
    """Return the annotated example config seed (source of truth).

    The committed `configs/pf-agent.example.yaml` is byte-identical to this;
    `pf-agent init --config` writes this text. No real secrets — provider keys
    are referenced indirectly via `api_key_ref` and resolved from the
    environment or the OS keyring at runtime.
    """
    return _EXAMPLE_CONFIG_TEXT


_EXAMPLE_CONFIG_TEXT = """\
# ProseForge Agent — example configuration (Task 195).
# Copy to `.pf-agent/config.yaml` (or generate with `pf-agent init --config`)
# and edit. Secrets are NOT stored here: providers reference a key by name via
# `api_key_ref`, resolved from the environment (.env) or the OS keyring.

setup:
  # Whether guided setup finished. `pf-agent setup` flips this to true.
  completed: false
  # Onboarding depth: minimal | standard | full.
  mode: minimal

agent:
  # Named behavior profile.
  profile: default
  # UI / drafting language (e.g. zh-CN, en-US).
  language: zh-CN
  # System-prompt template id from the prompt registry.
  system_prompt_template: professional_novel_editor

llm:
  # Provider used by default when a command does not name one.
  default_provider: fake
  # Provider used when the primary is unavailable (keep offline-safe).
  fallback_provider: fake
  # Provider registry. `fake` is deterministic and needs no key.
  providers:
    fake:
      enabled: true
      configured: true
      kind: fake
      model: fake
      status: ok
    openai:
      enabled: false
      configured: false
      kind: llm
      model: gpt-4o-mini
      status: unconfigured
      # Name of the env var / keyring entry holding the key (never the key).
      api_key_ref: OPENAI_API_KEY

paths:
  # Portable workspace root the agent owns.
  workspace_root: .pf-agent

engine:
  # Enable the authoritative ProseForge engine boundary ($PROSEFORGE_ROOT).
  enabled: false
"""


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
        payload["api_key_ref"] = key_ref
    return payload


def _default_provider(providers: dict[str, dict[str, Any]]) -> str:
    for name, payload in providers.items():
        if name != "fake" and payload.get("enabled") and payload.get("configured"):
            return name
    return "fake"


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalize_provider_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if "key_ref" in normalized and "api_key_ref" not in normalized:
        normalized["api_key_ref"] = normalized.pop("key_ref")
    normalized.pop("api_key", None)
    return normalized


def _workspace_text(path: str | Path) -> str:
    return path if isinstance(path, str) else str(Path(path))


__all__ = [
    "SetupConfigGenerator",
    "example_config_text",
    "known_config_keys",
    "load_existing",
    "provider_entry",
    "redact_config_text",
]
