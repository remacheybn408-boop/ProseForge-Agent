"""Injectable HTTP transport for HTTP-based providers.

Providers depend on the :class:`HttpTransport` protocol, never on a concrete
HTTP client, so request/response shape can be tested offline with
:class:`FakeHttpTransport` and the real :class:`UrllibTransport` is used in
production. The real transport relies only on the standard library.
"""

from __future__ import annotations

import json as _json
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class HttpRequest:
    """One outbound HTTP POST with a JSON body."""

    url: str
    headers: dict[str, str]
    json: dict
    timeout: float


@dataclass
class HttpResponse:
    """An HTTP response with the raw body preserved as text."""

    status_code: int
    text: str


class HttpTimeout(Exception):
    """Raised by a transport when a request exceeds its timeout."""


class HttpTransport(Protocol):
    """Protocol every HTTP transport implements."""

    def post_json(self, request: HttpRequest) -> HttpResponse: ...

    def post_json_stream(self, request: HttpRequest) -> Iterator[str]: ...


class UrllibTransport:
    """Real transport built on the standard library ``urllib``."""

    def post_json(self, request: HttpRequest) -> HttpResponse:
        data = _json.dumps(request.json).encode("utf-8")
        req = urllib.request.Request(
            request.url, data=data, headers=request.headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout) as resp:
                body = resp.read().decode("utf-8")
                return HttpResponse(status_code=resp.status, text=body)
        except urllib.error.HTTPError as exc:  # non-2xx still carries a body
            body = exc.read().decode("utf-8") if exc.fp else ""
            return HttpResponse(status_code=exc.code, text=body)
        except TimeoutError as exc:
            raise HttpTimeout(str(exc)) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise HttpTimeout(str(exc)) from exc
            raise

    def post_json_stream(self, request: HttpRequest) -> Iterator[str]:
        data = _json.dumps(request.json).encode("utf-8")
        req = urllib.request.Request(
            request.url, data=data, headers=request.headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout) as resp:
                for raw in resp:
                    line = raw.decode("utf-8").rstrip("\n")
                    if line:
                        yield line
        except TimeoutError as exc:
            raise HttpTimeout(str(exc)) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise HttpTimeout(str(exc)) from exc
            raise


@dataclass
class FakeHttpTransport:
    """Offline transport that records requests and replays canned responses."""

    responses: list[HttpResponse] = field(default_factory=list)
    stream_lines: list[str] = field(default_factory=list)
    raises: Exception | None = None
    requests: list[HttpRequest] = field(default_factory=list)

    def post_json(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if self.raises is not None:
            raise self.raises
        if not self.responses:
            raise AssertionError("FakeHttpTransport has no queued responses")
        return self.responses.pop(0)

    def post_json_stream(self, request: HttpRequest) -> Iterator[str]:
        self.requests.append(request)
        if self.raises is not None:
            raise self.raises
        yield from self.stream_lines


__all__ = [
    "HttpRequest",
    "HttpResponse",
    "HttpTimeout",
    "HttpTransport",
    "UrllibTransport",
    "FakeHttpTransport",
]
