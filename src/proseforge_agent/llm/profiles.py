"""Provider profile schema and loader.

A :class:`ProviderProfile` is a uniform description of one provider — cloud,
gateway, or local — recording its family, wire protocol, endpoint, model, key
environment variable, capabilities, privacy class, and certification level.
Local profiles never require an API key, and capability fields default to
``"unknown"`` until a provider is certified (Tasks 18-27).

This module is pure data plus validation; it does not build provider
instances or touch the registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..errors import ConfigurationError

CAPABILITY_KEYS: tuple[str, ...] = ("text", "streaming", "json", "tools", "vision")
LOCAL_FAMILIES: frozenset[str] = frozenset(
    {"ollama", "lmstudio", "vllm", "llamacpp"}
)
LOCAL_PROTOCOL_PREFIX = "local_"
_REQUIRED_FIELDS = ("family", "protocol", "model")


@dataclass(frozen=True)
class ProviderProfile:
    """Uniform description of one configured provider profile."""

    name: str
    family: str
    protocol: str
    model: str
    base_url: str | None = None
    api_key_env: str | None = None
    capabilities: dict[str, str] = field(default_factory=dict)
    privacy_class: str = "unspecified"
    certification_level: str = "uncertified"


def _default_capabilities() -> dict[str, str]:
    return {key: "unknown" for key in CAPABILITY_KEYS}


def _infer_privacy_class(family: str, protocol: str) -> str:
    if protocol.startswith(LOCAL_PROTOCOL_PREFIX) or family in LOCAL_FAMILIES:
        return "local"
    return "unspecified"


def _build_profile(name: str, data: dict) -> ProviderProfile:
    if not isinstance(data, dict):
        raise ConfigurationError(f"provider {name!r} must be a mapping")
    for required in _REQUIRED_FIELDS:
        if not data.get(required):
            raise ConfigurationError(
                f"provider {name!r} is missing required field {required!r}"
            )

    capabilities = _default_capabilities()
    configured_caps = data.get("capabilities") or {}
    if not isinstance(configured_caps, dict):
        raise ConfigurationError(
            f"provider {name!r} capabilities must be a mapping"
        )
    capabilities.update({str(k): str(v) for k, v in configured_caps.items()})

    privacy_class = data.get("privacy_class") or _infer_privacy_class(
        data["family"], data["protocol"]
    )

    return ProviderProfile(
        name=name,
        family=data["family"],
        protocol=data["protocol"],
        model=data["model"],
        base_url=data.get("base_url"),
        api_key_env=data.get("api_key_env"),
        capabilities=capabilities,
        privacy_class=privacy_class,
        certification_level=data.get("certification_level", "uncertified"),
    )


def load_provider_profiles(path: str | Path) -> dict[str, ProviderProfile]:
    """Load and validate provider profiles from a YAML file."""
    text = Path(path).read_text(encoding="utf-8")
    loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ConfigurationError(f"provider profile file {path} must be a mapping")
    providers = loaded.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise ConfigurationError(
            f"provider profile file {path} must contain a non-empty 'providers' mapping"
        )
    return {name: _build_profile(name, data) for name, data in providers.items()}


__all__ = [
    "CAPABILITY_KEYS",
    "LOCAL_FAMILIES",
    "ProviderProfile",
    "load_provider_profiles",
]
