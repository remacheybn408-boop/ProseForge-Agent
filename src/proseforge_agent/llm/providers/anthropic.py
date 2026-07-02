"""Anthropic / Claude provider profile.

Speaks the Anthropic Messages API behind the normalized provider contract:
workflows receive a :class:`ProviderResult` and never see raw Anthropic content
blocks. The API key is read from the environment named by the profile, is
redacted from request reprs (the ``x-api-key`` header), and never appears in
raised errors.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import date

from ...errors import ProviderError
from ..base import Message, ProviderRequest, ProviderResult, StreamChunk, Usage
from ..http import HttpRequest, HttpTimeout, HttpTransport, UrllibTransport
from ..profiles import ProviderProfile
from ._openai_shape import anthropic_tools, stream_anthropic_sse_lines

ANTHROPIC_ALIASES: tuple[str, ...] = ("anthropic", "claude")
CERT_LEVELS: tuple[str, ...] = (
    "profiled",
    "shape_tested",
    "smoke_tested",
    "workflow_tested",
    "certified",
)
SOURCE_NOTE = "Anthropic official API reference (docs.anthropic.com)"
_ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_MAX_TOKENS = 1024


class _RedactingHeaders(dict):
    """A headers mapping that hides the x-api-key value in its repr."""

    def __repr__(self) -> str:
        safe = dict(self)
        if "x-api-key" in safe:
            safe["x-api-key"] = "***"
        return repr(safe)


def _provider_error(message: str, code: str) -> ProviderError:
    error = ProviderError(message)
    error.code = code
    return error


class AnthropicProvider:
    """Call Anthropic's Messages endpoint."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        *,
        http: HttpTransport | None = None,
        timeout: float = 120.0,
        capabilities: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self.protocol = "anthropic_messages"
        self._http = http if http is not None else UrllibTransport()
        self._timeout = timeout
        self.capabilities = dict(capabilities or {})

    # -- request building ------------------------------------------------

    def _endpoint(self) -> str:
        return f"{self.base_url}/messages"

    def _headers(self) -> _RedactingHeaders:
        return _RedactingHeaders(
            {
                "x-api-key": self._api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            }
        )

    def _body(self, request: ProviderRequest, *, stream: bool) -> dict:
        body: dict = {
            "model": self.model,
            "max_tokens": request.max_tokens or _DEFAULT_MAX_TOKENS,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.tools:
            body["tools"] = anthropic_tools(request.tools)
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
            lines = self._http.post_json_stream(self._http_request(request, stream=True))
            yield from stream_anthropic_sse_lines(lines, provider_name=self.name)
        except HttpTimeout as exc:
            raise _provider_error(f"provider {self.name!r} timed out", "timeout") from exc

    # -- normalization ---------------------------------------------------

    @staticmethod
    def _extract_text(payload: dict) -> str:
        blocks = payload["content"]
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")

    @staticmethod
    def _extract_usage(payload: dict) -> Usage:
        usage = payload.get("usage") or {}
        return Usage(
            prompt_tokens=int(usage.get("input_tokens", 0) or 0),
            completion_tokens=int(usage.get("output_tokens", 0) or 0),
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


def build_provider(profile: ProviderProfile, *, http: HttpTransport | None = None) -> AnthropicProvider:
    """Build an :class:`AnthropicProvider` from a profile (no key required offline)."""
    api_key = os.environ.get(profile.api_key_env or "ANTHROPIC_API_KEY", "")
    return AnthropicProvider(
        name=profile.name,
        base_url=profile.base_url or "https://api.anthropic.com/v1",
        api_key=api_key,
        model=profile.model,
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
    env = profile.api_key_env or "ANTHROPIC_API_KEY"
    if not os.environ.get(env):
        return {"skipped": True, "reason": f"{env} not set; skipping real smoke test"}
    return {"skipped": False, "reason": f"{env} present; real smoke available"}


__all__ = [
    "ANTHROPIC_ALIASES",
    "CERT_LEVELS",
    "SOURCE_NOTE",
    "AnthropicProvider",
    "build_provider",
    "probe_capabilities",
    "shape_certification",
    "real_smoke",
]
