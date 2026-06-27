"""Intent-driven retrieval router.

Workflows ask for context by intent (draft, review, rewrite, plan); the router
maps the intent to a default query when the caller does not supply one, then
returns ranked, explained evidence items. Token-budget packing happens in the
evidence pack builder.
"""

from __future__ import annotations

from dataclasses import dataclass

from .index import MemoryIndex

# Default query terms per intent, used when no explicit query is provided.
INTENT_QUERY_TERMS: dict[str, str] = {
    "chapter_draft": "canon promise character setting",
    "draft": "canon promise character setting",
    "plan": "arc promise structure",
    "review": "warning continuity contradiction risk",
    "rewrite": "style voice canon",
}
_DEFAULT_QUERY = "canon"


@dataclass(frozen=True)
class RetrievalRequest:
    """A context request expressed by intent."""

    project_slug: str
    intent: str
    chapter_no: int | None = None
    query: str | None = None
    token_budget: int = 1000


@dataclass(frozen=True)
class EvidenceItem:
    """A ranked piece of retrieved context with inclusion/exclusion reasons."""

    text: str
    source: str
    type: str
    score: float
    reason_included: str = ""
    reason_excluded: str = ""


class RetrievalRouter:
    """Turn an intent request into ranked, explained evidence items."""

    def __init__(self, index: MemoryIndex) -> None:
        self._index = index

    def query_for(self, request: RetrievalRequest) -> str:
        if request.query:
            return request.query
        return INTENT_QUERY_TERMS.get(request.intent, _DEFAULT_QUERY)

    def route(self, request: RetrievalRequest) -> list[EvidenceItem]:
        query = self.query_for(request)
        scored = self._index.search(request.project_slug, query)
        items: list[EvidenceItem] = []
        for entry in scored:
            item = entry.item
            reason = (
                f"matched intent {request.intent!r} via query {query!r} "
                f"(score {entry.score:g})"
            )
            items.append(
                EvidenceItem(
                    text=item.text,
                    source=item.source,
                    type=item.type,
                    score=entry.score,
                    reason_included=reason,
                )
            )
        return items


__all__ = ["RetrievalRequest", "EvidenceItem", "RetrievalRouter", "INTENT_QUERY_TERMS"]
