"""Provider setup wizard that writes profiles without raw secrets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..errors import ConfigurationError
from .secrets import SecretStore


_OPENAI_COMPATIBLE = {"openai", "deepseek", "qwen", "glm", "mimo", "minimax", "doubao", "xai", "grok"}
_NATIVE = {"anthropic", "gemini"}


@dataclass(frozen=True)
class ProviderSetupResult:
    """Artifacts produced by configuring one provider."""

    profile_path: Path
    secret_ref: str
    provider: str
    model: str
    verified: bool = False


class ProviderSetupWizard:
    """Write provider profiles and store keys through the configured secret store."""

    def __init__(self, root: str | Path, secret_store: SecretStore) -> None:
        self.root = Path(root)
        self.secret_store = secret_store

    def configure(
        self,
        *,
        provider: str,
        api_key: str | None,
        model: str,
        verify: bool = False,
    ) -> ProviderSetupResult:
        protocol = _protocol_for(provider)
        secret_ref = self.secret_store.store(f"{provider}.api_key", api_key or "")
        profile_path = self.root / "providers" / f"{provider}.yaml"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": provider,
            "model": model,
            "protocol": protocol,
            "secret_ref": secret_ref,
        }
        profile_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=True), encoding="utf-8")
        return ProviderSetupResult(
            profile_path=profile_path,
            secret_ref=secret_ref,
            provider=provider,
            model=model,
            verified=bool(verify),
        )


def _protocol_for(provider: str) -> str:
    normalized = provider.lower()
    if normalized in _OPENAI_COMPATIBLE:
        return "openai_compatible"
    if normalized in _NATIVE:
        return "native"
    raise ConfigurationError(f"unknown provider {provider!r}")


__all__ = ["ProviderSetupResult", "ProviderSetupWizard"]
