"""OpenAI-compatible chat provider transport.

Shared by domestic, foreign, local, and gateway endpoints that speak the
OpenAI ``/chat/completions`` shape. Vendor-specific certification lives in
later tasks; this module only implements the protocol and normalizes errors.

API keys are never included in raised error messages.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

from ..errors import ProviderError
from .base import (
    Message,
    ProviderRequest,
    ProviderResult,
    StreamChunk,
    Usage,
)
from .http import HttpRequest, HttpTimeout, HttpTransport, UrllibTransport
from .providers._openai_shape import add_openai_tools, openai_message_text, stream_openai_sse_lines


def _provider_error(message: str, code: str) -> ProviderError:
    error = ProviderError(message)
    error.code = code
    return error


class OpenAICompatibleProvider:
    """Call an OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        *,
        http: HttpTransport | None = None,
        timeout: float = 120.0,
        extra_body: dict | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self._http = http if http is not None else UrllibTransport()
        self._timeout = timeout
        self._extra_body = dict(extra_body or {})

    # -- request building -------------------------------------------------

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _body(self, request: ProviderRequest, *, stream: bool) -> dict:
        body: dict = {
            "model": self.model,
            "messages": [
                {"role": m.role, "content": m.content} for m in request.messages
            ],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        add_openai_tools(body, request.tools)
        if stream:
            body["stream"] = True
        body.update(self._extra_body)
        return body

    def _request(self, request: ProviderRequest, *, stream: bool) -> HttpRequest:
        return HttpRequest(
            url=self._endpoint(),
            headers=self._headers(),
            json=self._body(request, stream=stream),
            timeout=self._timeout,
        )

    # -- generation -------------------------------------------------------

    def generate(self, request: ProviderRequest) -> ProviderResult:
        try:
            response = self._http.post_json(self._request(request, stream=False))
        except HttpTimeout as exc:
            raise _provider_error(f"provider {self.name!r} timed out", "timeout") from exc

        if response.status_code >= 400:
            raise self._error_for_status(response.status_code)

        try:
            payload = json.loads(response.text)
            text = openai_message_text(payload)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise _provider_error(
                f"provider {self.name!r} returned an unparseable response",
                "invalid_response",
            ) from exc

        usage_data = payload.get("usage") or {}
        usage = Usage(
            prompt_tokens=int(usage_data.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage_data.get("completion_tokens", 0) or 0),
        )
        return ProviderResult(
            provider=self.name,
            model=payload.get("model", self.model),
            text=text,
            usage=usage,
            raw=payload,
        )

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]:
        try:
            lines = self._http.post_json_stream(self._request(request, stream=True))
            yield from stream_openai_sse_lines(
                lines,
                provider_name=self.name,
                extract_delta=self._extract_delta,
            )
        except HttpTimeout as exc:
            raise _provider_error(f"provider {self.name!r} timed out", "timeout") from exc

    @staticmethod
    def _extract_delta(obj: dict) -> str:
        return obj["choices"][0]["delta"].get("content", "") or ""

    # -- errors -----------------------------------------------------------

    def _error_for_status(self, status: int) -> ProviderError:
        if status == 401:
            return _provider_error(
                f"provider {self.name!r} rejected authentication (401)", "auth"
            )
        if status == 429:
            return _provider_error(
                f"provider {self.name!r} is rate limited (429)", "rate_limit"
            )
        if status >= 500:
            return _provider_error(
                f"provider {self.name!r} server error ({status})", "server_error"
            )
        return _provider_error(
            f"provider {self.name!r} request failed ({status})", "provider_error"
        )


__all__ = ["OpenAICompatibleProvider"]
