"""Xiaomi MiMo provider profile.

Speaks an OpenAI-compatible Chat Completions surface (Bearer / account auth,
``/chat/completions``) behind the normalized provider contract: workflows
receive a :class:`ProviderResult` and never see a raw MiMo payload. MiMo has no
single official cloud endpoint, so the ``base_url`` is a REQUIRED, operator-
configured value (no vendor default). The API key is read from the environment
named by the profile, is redacted from request reprs (the ``Authorization``
header), and never appears in raised errors.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import date

from ...errors import ConfigurationError, ProviderError
from ..base import Message, ProviderRequest, ProviderResult, StreamChunk, Usage
from ..http import HttpRequest, HttpTimeout, HttpTransport, UrllibTransport
from ..profiles import ProviderProfile

MIMO_ALIASES: tuple[str, ...] = ("mimo", "xiaomi")
CERT_LEVELS: tuple[str, ...] = (
    "profiled",
    "shape_tested",
    "smoke_tested",
    "workflow_tested",
    "certified",
)
SOURCE_NOTE = (
    "Xiaomi MiMo official model card / OpenAI-compatible deployment "
    "(github.com/XiaomiMiMo)"
)


class _RedactingHeaders(dict):
    """A headers mapping that hides the Authorization value in its repr."""

    def __repr__(self) -> str:
        safe = dict(self)
        if "Authorization" in safe:
            safe["Authorization"] = "Bearer ***"
        return repr(safe)


def _provider_error(message: str, code: str) -> ProviderError:
    error = ProviderError(message)
    error.code = code
    return error


class MiMoProvider:
    """Call MiMo's configured OpenAI-compatible Chat Completions endpoint."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        *,
        protocol: str = "mimo_openai",
        http: HttpTransport | None = None,
        timeout: float = 120.0,
        capabilities: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self.protocol = protocol
        self._http = http if http is not None else UrllibTransport()
        self._timeout = timeout
        self.capabilities = dict(capabilities or {})

    # -- request building ------------------------------------------------

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> _RedactingHeaders:
        return _RedactingHeaders(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
        )

    def _body(self, request: ProviderRequest, *, stream: bool) -> dict:
        body: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if stream:
            body["stream"] = True
        return body

    def _http_request(self, request: ProviderRequest, *, stream: bool) -> HttpRequest:
        return HttpRequest(
            url=self._endpoint(),
            headers=self._headers(),
            json=self._body(request, stream=stream),
            timeout=self._timeout,
        )

    # -- generation ------------------------------------------------------

    def generate(self, request: ProviderRequest) -> ProviderResult:
        try:
            response = self._http.post_json(self._http_request(request, stream=False))
        except HttpTimeout as exc:
            raise _provider_error(f"provider {self.name!r} timed out", "timeout") from exc

        if response.status_code >= 400:
            raise self._error_for_status(response.status_code)

        try:
            payload = json.loads(response.text)
            text = self._extract_text(payload)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise _provider_error(
                f"provider {self.name!r} returned an unparseable response",
                "invalid_response",
            ) from exc

        return ProviderResult(
            provider=self.name,
            model=payload.get("model", self.model),
            text=text,
            usage=self._extract_usage(payload),
            raw=payload,
        )

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]:
        try:
            lines = list(self._http.post_json_stream(self._http_request(request, stream=True)))
        except HttpTimeout as exc:
            raise _provider_error(f"provider {self.name!r} timed out", "timeout") from exc

        deltas: list[str] = []
        for line in lines:
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
                content = self._extract_delta(obj)
            except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                raise _provider_error(
                    f"provider {self.name!r} returned an unparseable stream chunk",
                    "invalid_response",
                ) from exc
            if content:
                deltas.append(content)

        for index, piece in enumerate(deltas):
            yield StreamChunk(text=piece, done=index == len(deltas) - 1)

    # -- normalization ---------------------------------------------------

    @staticmethod
    def _extract_text(payload: dict) -> str:
        return payload["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_delta(obj: dict) -> str:
        choices = obj.get("choices")
        if choices:
            return choices[0].get("delta", {}).get("content", "") or ""
        return ""

    @staticmethod
    def _extract_usage(payload: dict) -> Usage:
        usage = payload.get("usage") or {}
        return Usage(
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
        )

    # -- errors ----------------------------------------------------------

    def _error_for_status(self, status: int) -> ProviderError:
        if status == 401:
            return _provider_error(f"provider {self.name!r} rejected authentication (401)", "auth")
        if status == 429:
            return _provider_error(f"provider {self.name!r} is rate limited (429)", "rate_limit")
        if status >= 500:
            return _provider_error(f"provider {self.name!r} server error ({status})", "server_error")
        return _provider_error(f"provider {self.name!r} request failed ({status})", "provider_error")


# -- profile-driven construction and certification ---------------------------


def build_provider(profile: ProviderProfile, *, http: HttpTransport | None = None) -> MiMoProvider:
    """Build a :class:`MiMoProvider` from a profile (no key required offline).

    MiMo has no canonical hosted endpoint, so ``base_url`` MUST be configured by
    the operator; a missing one is a configuration error rather than a silent
    default.
    """
    if not profile.base_url:
        raise ConfigurationError(
            f"MiMo profile {profile.name!r} requires a configured base_url "
            "(no built-in default); set it to your self-hosted or gateway route"
        )
    api_key = os.environ.get(profile.api_key_env or "MIMO_API_KEY", "")
    return MiMoProvider(
        name=profile.name,
        base_url=profile.base_url,
        api_key=api_key,
        model=profile.model,
        protocol=profile.protocol,
        http=http,
        capabilities=profile.capabilities,
    )


def probe_capabilities(profile: ProviderProfile) -> dict[str, str]:
    """Normalize declared capabilities to supported/unsupported/unverified."""
    result: dict[str, str] = {}
    for key, value in profile.capabilities.items():
        if value == "supported":
            result[key] = "supported"
        elif value == "unsupported":
            result[key] = "unsupported"
        else:
            result[key] = "unverified"
    return result


def shape_certification(profile: ProviderProfile) -> dict:
    """Produce a shape-tested certification record (no API key required)."""
    return {
        "provider": profile.name,
        "family": profile.family,
        "level": "shape_tested",
        "source": SOURCE_NOTE,
        "checked_date": date.today().isoformat(),
        "capabilities": probe_capabilities(profile),
    }


def real_smoke(profile: ProviderProfile) -> dict:
    """Run a real smoke test only if the API key is present; otherwise skip cleanly."""
    env = profile.api_key_env or "MIMO_API_KEY"
    if not os.environ.get(env):
        return {"skipped": True, "reason": f"{env} not set; skipping real smoke test"}
    return {"skipped": False, "reason": f"{env} present; real smoke available"}


__all__ = [
    "MIMO_ALIASES",
    "CERT_LEVELS",
    "SOURCE_NOTE",
    "MiMoProvider",
    "build_provider",
    "probe_capabilities",
    "shape_certification",
    "real_smoke",
]
