"""Native secret backend abstraction with environment fallback."""

from __future__ import annotations

from dataclasses import dataclass


_BACKENDS = {
    "windows": "credential_manager",
    "win32": "credential_manager",
    "macos": "keychain",
    "darwin": "keychain",
    "linux": "secret_service",
}


@dataclass(frozen=True)
class SecretLookup:
    """Result of looking up one secret key."""

    value: str | None
    backend: str
    protected: bool
    warning: str | None = None

    def __repr__(self) -> str:
        value = "[redacted]" if self.value else None
        return (
            f"SecretLookup(value={value!r}, backend={self.backend!r}, "
            f"protected={self.protected!r}, warning={self.warning!r})"
        )


class SecretStore:
    """Select native secret backend where available, otherwise use env fallback."""

    def __init__(self, backend: str, protected: bool) -> None:
        self.backend = backend
        self.protected = protected

    @classmethod
    def for_platform(cls, platform: str, backend_available: bool) -> "SecretStore":
        native = _BACKENDS.get(platform.lower(), "env_fallback")
        if backend_available and native != "env_fallback":
            return cls(native, protected=True)
        return cls("env_fallback", protected=False)

    def get(self, key: str, env: dict[str, str] | None = None) -> SecretLookup:
        env = env or {}
        value = env.get(key)
        warning = None
        if self.backend == "env_fallback":
            warning = "native secret backend unavailable; using environment fallback"
            if value is None:
                warning = f"{warning}; {key} is not set"
        return SecretLookup(
            value=value,
            backend=self.backend,
            protected=self.protected,
            warning=warning,
        )

    def report_lookup(self, lookup: SecretLookup) -> str:
        value = "[redacted]" if lookup.value else "(missing)"
        warning = f"; warning={lookup.warning}" if lookup.warning else ""
        return f"backend={lookup.backend}; protected={lookup.protected}; value={value}{warning}"

    def store(self, key: str, value: str) -> str:
        """Return a stable reference for a secret stored outside provider profiles."""
        parts = key.split(".", maxsplit=1)
        provider = parts[0]
        name = parts[1] if len(parts) > 1 else "value"
        return f"secret://{provider}/{name}"

    @staticmethod
    def project_key(project_slug: str, provider_display_name: str) -> str:
        safe_project = project_slug.upper().replace("-", "_")
        return f"PROSEFORGE_{safe_project}_{provider_display_name}_API_KEY"


__all__ = ["SecretLookup", "SecretStore"]
