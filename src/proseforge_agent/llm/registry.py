"""Provider registry: resolve a role to a configured provider instance.

The registry is the single workflow-facing entry point for model access.
Workflows ask for a role (``planner``, ``drafter``, ...) and receive an
:class:`LLMProvider`; they never name a concrete provider or API kind.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import yaml

from ..errors import ConfigurationError
from .base import LLMProvider, ProviderSpec
from .fake import FakeProvider
from .profiles import ProviderProfile
from .providers.openai import OPENAI_ALIASES, build_provider as _build_openai
from .providers.anthropic import ANTHROPIC_ALIASES, build_provider as _build_anthropic
from .http import HttpTransport

# Profile-driven builders keyed by provider family / protocol alias. Concrete
# vendor profiles (OpenAI, Anthropic, ...) register here; the fake/kind path is
# separate.
PROFILE_BUILDERS: dict[str, Callable[..., LLMProvider]] = {
    **{alias: _build_openai for alias in OPENAI_ALIASES},
    **{alias: _build_anthropic for alias in ANTHROPIC_ALIASES},
    "anthropic_messages": _build_anthropic,
}


def build_provider_from_profile(
    profile: ProviderProfile, *, http: HttpTransport | None = None
) -> LLMProvider:
    """Resolve a :class:`ProviderProfile` to a concrete provider via its family/protocol."""
    for key in (profile.family, profile.protocol):
        builder = PROFILE_BUILDERS.get(key)
        if builder is not None:
            return builder(profile, http=http)
    raise ConfigurationError(
        f"no provider builder for family {profile.family!r} / protocol {profile.protocol!r}"
    )


def _build_fake(spec: ProviderSpec) -> LLMProvider:
    return FakeProvider(name=spec.name, model=spec.model)


# Real kinds (openai_compatible, native) register their factories in later tasks.
_PROVIDER_FACTORIES: dict[str, Callable[[ProviderSpec], LLMProvider]] = {
    "fake": _build_fake,
}


class ProviderRegistry:
    """Resolve roles to provider instances from declarative config."""

    def __init__(
        self,
        specs: dict[str, ProviderSpec],
        roles: dict[str, str],
        default_provider: str,
    ) -> None:
        self._specs = specs
        self._roles = roles
        self._default_provider = default_provider
        self._instances: dict[str, LLMProvider] = {}
        self._validate()

    def _validate(self) -> None:
        if self._default_provider not in self._specs:
            raise ConfigurationError(
                f"default_provider {self._default_provider!r} is not a configured provider"
            )
        for role, name in self._roles.items():
            if name not in self._specs:
                raise ConfigurationError(
                    f"role {role!r} maps to unknown provider {name!r}"
                )

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderRegistry":
        providers = data.get("providers") or []
        specs: dict[str, ProviderSpec] = {}
        for entry in providers:
            spec = ProviderSpec(
                name=entry["name"],
                kind=entry["kind"],
                model=entry.get("model", ""),
                options=entry.get("options") or {},
            )
            specs[spec.name] = spec
        roles = data.get("roles") or {}
        default_provider = data.get("default_provider")
        if not default_provider:
            raise ConfigurationError("default_provider is required")
        return cls(specs=specs, roles=roles, default_provider=default_provider)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ProviderRegistry":
        text = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ConfigurationError(f"provider config {path} must be a mapping")
        return cls.from_dict(data)

    def provider_for_role(self, role: str) -> LLMProvider:
        name = self._roles.get(role, self._default_provider)
        if name not in self._specs:
            raise ConfigurationError(f"unknown provider {name!r} for role {role!r}")
        return self._instance(name)

    def _instance(self, name: str) -> LLMProvider:
        if name not in self._instances:
            spec = self._specs[name]
            factory = _PROVIDER_FACTORIES.get(spec.kind)
            if factory is None:
                raise ConfigurationError(
                    f"provider {name!r} has unsupported kind {spec.kind!r}"
                )
            self._instances[name] = factory(spec)
        return self._instances[name]


__all__ = ["ProviderRegistry", "build_provider_from_profile", "PROFILE_BUILDERS"]
