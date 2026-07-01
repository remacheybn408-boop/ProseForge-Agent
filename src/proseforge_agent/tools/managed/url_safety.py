"""URL safety checks for managed web tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class UrlSafetyDecision:
    """Safety classification for a URL before managed network use."""

    status: str
    url: str
    reason: str
    domain: str = ""
    mime_type: str = ""
    content_length: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "url": self.url,
            "reason": self.reason,
            "domain": self.domain,
            "mime_type": self.mime_type,
            "content_length": self.content_length,
        }


class UrlSafetyPolicy:
    """Allow/deny policy for managed URL inspection and search results."""

    def __init__(
        self,
        *,
        allowed_domains: set[str] | None = None,
        denied_domains: set[str] | None = None,
        allowed_mime_types: set[str] | None = None,
        max_content_bytes: int = 5_000_000,
        network_enabled: bool = True,
    ) -> None:
        self.allowed_domains = set(allowed_domains or set())
        self.denied_domains = set(denied_domains or set())
        self.allowed_mime_types = set(
            allowed_mime_types or {"text/html", "text/plain", "application/json"}
        )
        self.max_content_bytes = max_content_bytes
        self.network_enabled = network_enabled

    def check(
        self,
        url: str,
        *,
        mime_type: str = "text/html",
        content_length: int = 0,
    ) -> UrlSafetyDecision:
        parsed = urlparse(str(url))
        domain = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"}:
            return self._decision("blocked", url, "only http and https URLs are allowed", domain, mime_type, content_length)
        if not self.network_enabled:
            return self._decision("unsupported", url, "network access is disabled", domain, mime_type, content_length)
        if self._matches(domain, self.denied_domains):
            return self._decision("blocked", url, f"domain {domain} is denied", domain, mime_type, content_length)
        if self.allowed_domains and not self._matches(domain, self.allowed_domains):
            return self._decision("blocked", url, f"domain {domain} is not allowed", domain, mime_type, content_length)
        if mime_type and mime_type not in self.allowed_mime_types:
            return self._decision("unsupported", url, f"mime type {mime_type} is unsupported", domain, mime_type, content_length)
        if content_length and content_length > self.max_content_bytes:
            return self._decision(
                "blocked",
                url,
                f"content length {content_length} exceeds limit {self.max_content_bytes}",
                domain,
                mime_type,
                content_length,
            )
        return self._decision("allowed", url, "URL passed safety policy", domain, mime_type, content_length)

    @staticmethod
    def _matches(domain: str, configured: set[str]) -> bool:
        return any(domain == item or domain.endswith(f".{item}") for item in configured)

    @staticmethod
    def _decision(
        status: str,
        url: str,
        reason: str,
        domain: str,
        mime_type: str,
        content_length: int,
    ) -> UrlSafetyDecision:
        return UrlSafetyDecision(
            status=status,
            url=url,
            reason=reason,
            domain=domain,
            mime_type=mime_type,
            content_length=content_length,
        )


__all__ = ["UrlSafetyDecision", "UrlSafetyPolicy"]
