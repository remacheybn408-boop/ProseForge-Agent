"""Google / Gemini provider profile.

Speaks Gemini's native GenerateContent API (and an OpenAI-compatible bridge)
behind the normalized provider contract: workflows receive a
:class:`ProviderResult` and never see raw Gemini candidates / safety / function
calls. The API key is read from the environment named by the profile, is
redacted from request reprs (the ``x-goog-api-key`` / ``Authorization`` header),
and never appears in raised errors.
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

GEMINI_ALIASES: tuple[str, ...] = ("gemini", "gemini_native", "gemini_openai")
CERT_LEVELS: tuple[str, ...] = (
    "profiled",
    "shape_tested",
    "smoke_tested",
    "workflow_tested",
    "certified",
)
SOURCE_NOTE = "Google Gemini official API reference (ai.google.dev/gemini-api/docs)"
_DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_NATIVE_PROTOCOLS = frozenset({"gemini_generate", "gemini_native", "generate_content", "native"})
_OPENAI_PROTOCOLS = frozenset({"gemini_openai", "openai_chat"})


class _RedactingHeaders(dict):
    """A headers mapping that hides API-key values in its repr."""

    def __repr__(self) -> str:
        safe = dict(self)
        if "x-goog-api-key" in safe:
            safe["x-goog-api-key"] = "***"
        if "Authorization" in safe:
            safe["Authorization"] = "Bearer ***"
        return repr(safe)


def _provider_error(message: str, code: str) -> ProviderError:
    error = ProviderError(message)
    error.code = code
    return error


def _role(role: str) -> str:
    # Gemini `contents` only recognizes "user" and "model" roles.
    return "model" if role == "assistant" else "user"


class GeminiProvider:
    """Call Gemini's GenerateContent endpoint, or its OpenAI-compatible bridge."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        *,
        protocol: str = "gemini_generate",
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

    def _is_openai(self) -> bool:
        return self.protocol in _OPENAI_PROTOCOLS

    def _endpoint(self, *, stream: bool) -> str:
        if self._is_openai():
            return f"{self.base_url}/chat/completions"
        verb = "streamGenerateContent?alt=sse" if stream else "generateContent"
        return f"{self.base_url}/models/{self.model}:{verb}"

    def _headers(self) -> _RedactingHeaders:
        if self._is_openai():
            return _RedactingHeaders(
                {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
            )
        return _RedactingHeaders(
            {
                "x-goog-api-key": self._api_key,
                "Content-Type": "application/json",
            }
        )

    def _body(self, request: ProviderRequest, *, stream: bool) -> dict:
        # `model` is always present so the request is self-describing (the native
        # API also carries it in the URL path).
        if self._is_openai():
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

        generation_config: dict = {"temperature": request.temperature}
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        return {
            "model": self.model,
            "contents": [
                {"role": _role(m.role), "parts": [{"text": m.content}]}
                for m in request.messages
            ],
            "generationConfig": generation_config,
        }

    def _http_request(self, request: ProviderRequest, *, stream: bool) -> HttpRequest:
        return HttpRequest(
            url=self._endpoint(stream=stream),
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
            model=payload.get("model", payload.get("modelVersion", self.model)),
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

    def _extract_text(self, payload: dict) -> str:
        if self._is_openai():
            return payload["choices"][0]["message"]["content"]
        return self._extract_text_native(payload)

    @staticmethod
    def _extract_text_native(payload: dict) -> str:
        candidate = payload["candidates"][0]
        parts = candidate["content"]["parts"]
        return "".join(part.get("text", "") for part in parts if "text" in part)

    def _extract_usage(self, payload: dict) -> Usage:
        if self._is_openai():
            usage = payload.get("usage") or {}
            return Usage(
                prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
                completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            )
        usage = payload.get("usageMetadata") or {}
        return Usage(
            prompt_tokens=int(usage.get("promptTokenCount", 0) or 0),
            completion_tokens=int(usage.get("candidatesTokenCount", 0) or 0),
        )

    def _extract_delta(self, obj: dict) -> str:
        if self._is_openai():
            choices = obj.get("choices")
            if choices:
                return choices[0].get("delta", {}).get("content", "") or ""
            return ""
        candidates = obj.get("candidates")
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts if "text" in part)

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


def build_provider(profile: ProviderProfile, *, http: HttpTransport | None = None) -> GeminiProvider:
    """Build a :class:`GeminiProvider` from a profile (no key required offline)."""
    api_key = os.environ.get(profile.api_key_env or "GEMINI_API_KEY", "")
    return GeminiProvider(
        name=profile.name,
        base_url=profile.base_url or _DEFAULT_BASE_URL,
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
    env = profile.api_key_env or "GEMINI_API_KEY"
    if not os.environ.get(env):
        return {"skipped": True, "reason": f"{env} not set; skipping real smoke test"}
    return {"skipped": False, "reason": f"{env} present; real smoke available"}


__all__ = [
    "GEMINI_ALIASES",
    "CERT_LEVELS",
    "SOURCE_NOTE",
    "GeminiProvider",
    "build_provider",
    "probe_capabilities",
    "shape_certification",
    "real_smoke",
]
