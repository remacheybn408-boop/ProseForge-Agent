"""Deterministic keyword index over Agent memory.

A first-version retrieval index that scores active memory items by keyword
overlap against a query. Scoring runs in Python rather than SQLite FTS5 because
the default FTS5 tokenizer does not segment Chinese text; substring/term
scoring works for CJK and stays deterministic for tests. The ``scorer`` slot is
an extension point for a future semantic (embedding) scorer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..memory.store import MemoryItem, MemoryStore


@dataclass(frozen=True)
class ScoredItem:
    """A memory item with its retrieval score."""

    item: MemoryItem
    score: float


def _terms(query: str) -> list[str]:
    return [t for t in query.casefold().split() if t]


def keyword_scorer(query_terms: list[str], item: MemoryItem) -> float:
    """Score by how many query terms appear in the item text or tags."""
    text = item.text.casefold()
    tags = [tag.casefold() for tag in item.tags]
    score = 0.0
    for term in query_terms:
        if term in text:
            score += 1.0
        if any(term in tag for tag in tags):
            score += 0.5
    return score


Scorer = Callable[[list[str], MemoryItem], float]


class MemoryIndex:
    """Rank active memory items for a project by keyword relevance."""

    def __init__(self, store: MemoryStore, *, scorer: Scorer | None = None) -> None:
        self._store = store
        self._scorer = scorer or keyword_scorer

    def search(
        self, project_slug: str, query: str, *, limit: int | None = None
    ) -> list[ScoredItem]:
        terms = _terms(query)
        items = self._store.list(project_slug=project_slug, status="active")
        scored = [ScoredItem(item=item, score=self._scorer(terms, item)) for item in items]
        scored.sort(key=lambda s: (-s.score, s.item.id))
        if limit is not None:
            scored = scored[:limit]
        return scored


__all__ = ["ScoredItem", "MemoryIndex", "keyword_scorer"]
