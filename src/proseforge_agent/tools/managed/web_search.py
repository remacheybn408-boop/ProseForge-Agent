"""Deterministic managed web search tools."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class WebSearchResult:
    """One citation candidate returned by managed web search."""

    citation_id: str
    title: str
    url: str
    snippet: str
    source: str = "fake_web"
    score: float = 1.0
    is_canon: bool = False

    def to_citation(self) -> dict[str, Any]:
        return {
            "id": self.citation_id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "snippet": self.snippet,
            "is_canon": self.is_canon,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "score": self.score,
            "is_canon": self.is_canon,
        }


@dataclass(frozen=True)
class WebSearchResponse:
    """Search response with canon-safe citation metadata."""

    query: str
    results: list[WebSearchResult]
    provider: str = "fake"
    degraded: bool = False
    reason: str = ""

    @property
    def citations(self) -> list[dict[str, Any]]:
        return [result.to_citation() for result in self.results]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "provider": self.provider,
            "degraded": self.degraded,
            "reason": self.reason,
            "results": [result.to_dict() for result in self.results],
            "citations": self.citations,
        }


class FakeWebSearchProvider:
    """Offline deterministic web search provider for tests and demos."""

    def search(self, query: str, *, limit: int = 3) -> WebSearchResponse:
        clean_query = " ".join(str(query).split())
        if not clean_query:
            return WebSearchResponse(
                query="",
                results=[],
                degraded=True,
                reason="query is required",
            )

        slug = _slugify(clean_query)
        results = [
            WebSearchResult(
                citation_id=f"web-{index}",
                title=f"{clean_query} reference {index}",
                url=f"https://example.com/search/{slug}/{index}",
                snippet=f"Deterministic citation candidate for {clean_query} ({index}).",
                score=1.0 / index,
            )
            for index in range(1, max(1, limit) + 1)
        ]
        return WebSearchResponse(query=clean_query, results=results[:limit])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "query"


__all__ = ["FakeWebSearchProvider", "WebSearchResponse", "WebSearchResult"]
