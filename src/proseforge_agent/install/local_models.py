"""Offline discovery helpers for local OpenAI-compatible model servers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .secrets import SecretStore


DEFAULT_LOCAL_MODEL_ENDPOINTS = (
    "http://127.0.0.1:11434",
    "http://127.0.0.1:1234",
    "http://127.0.0.1:8000",
)


class JsonHttpClient(Protocol):
    """Minimal injected client shape used by local model discovery."""

    def get_json(self, url: str) -> object:
        """Return decoded JSON from ``url``."""


@dataclass(frozen=True)
class LocalModelCandidate:
    """One reachable local model server candidate."""

    endpoint: str
    models: list[str]
    privacy: str = "local"
    profile_shape: str = "openai_compatible"
    note: str = "discovered through injected http client"


class LocalModelDetector:
    """Detect local model servers without owning any network implementation."""

    def __init__(
        self,
        http: JsonHttpClient,
        secret_store: SecretStore | None = None,
    ) -> None:
        self.http = http
        self.secret_store = secret_store
        self.notes: list[str] = []

    def detect(self, endpoints: list[str] | tuple[str, ...] | None = None) -> list[LocalModelCandidate]:
        """Return candidates from injected HTTP responses, skipping failures."""
        endpoints = endpoints or DEFAULT_LOCAL_MODEL_ENDPOINTS
        candidates: list[LocalModelCandidate] = []
        self.notes.clear()
        for endpoint in endpoints:
            base = endpoint.rstrip("/")
            url = f"{base}/v1/models"
            try:
                payload = self.http.get_json(url)
            except Exception as exc:  # pragma: no cover - exact client error is injected
                self.notes.append(f"{base}: unavailable ({exc})")
                continue
            models = self._extract_models(payload)
            if not models:
                self.notes.append(f"{base}: reachable but no models reported")
                continue
            candidates.append(LocalModelCandidate(endpoint=base, models=models))
        return candidates

    def store_token(self, provider: str, token: str) -> str:
        """Store a local server token through the configured secret store."""
        store = self.secret_store or SecretStore.for_platform("linux", False)
        return store.store(f"{provider}.api_key", token)

    @staticmethod
    def _extract_models(payload: object) -> list[str]:
        if not isinstance(payload, dict):
            return []
        raw_models = payload.get("models")
        if raw_models is None:
            raw_models = payload.get("data")
        if not isinstance(raw_models, list):
            return []
        models: list[str] = []
        for item in raw_models:
            if isinstance(item, str):
                models.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or item.get("id")
                if isinstance(name, str) and name:
                    models.append(name)
        return models


__all__ = [
    "DEFAULT_LOCAL_MODEL_ENDPOINTS",
    "JsonHttpClient",
    "LocalModelCandidate",
    "LocalModelDetector",
]
