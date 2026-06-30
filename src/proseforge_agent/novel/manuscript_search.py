"""Whole-manuscript search across chapters, scenes, drafts, and story-bible artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# Prose domains searched by the default ``manuscript`` scope.
_MANUSCRIPT_DIRS = ("chapters", "scenes", "drafts", "revisions", "final")
# Additional reference domains added by the ``all`` scope.
_EXTRA_DIRS = ("bible", "timeline", "plot_threads", "comments")

_SEARCHABLE_SUFFIXES = (".md", ".txt", ".yaml", ".yml", ".json")

SEARCH_SCOPES = ("manuscript", "all")


@dataclass(frozen=True)
class SearchHit:
    """One matching line within a manuscript artifact."""

    domain: str
    chapter: str
    path: str
    line: int
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult:
    """Ordered search hits for one query."""

    query: str
    scope: str
    exact: bool
    hits: list[SearchHit] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.hits)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "scope": self.scope,
            "exact": self.exact,
            "count": self.count,
            "hits": [hit.to_dict() for hit in self.hits],
        }


class ManuscriptSearch:
    """Search the whole manuscript, not just memory retrieval."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def search(self, query: str, *, scope: str = "manuscript", exact: bool = False) -> SearchResult:
        if scope not in SEARCH_SCOPES:
            raise ValueError(f"unknown search scope {scope!r}; use one of {SEARCH_SCOPES}")
        if not query:
            raise ValueError("query must not be empty")
        domains = _MANUSCRIPT_DIRS if scope == "manuscript" else _MANUSCRIPT_DIRS + _EXTRA_DIRS
        needle = query if exact else query.casefold()
        hits: list[SearchHit] = []
        for domain in domains:
            domain_root = self.project_root / domain
            if not domain_root.exists():
                continue
            for path in sorted(domain_root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in _SEARCHABLE_SUFFIXES:
                    continue
                hits.extend(self._scan_file(path, domain=domain, needle=needle, exact=exact))
        return SearchResult(query=query, scope=scope, exact=exact, hits=hits)

    def _scan_file(self, path: Path, *, domain: str, needle: str, exact: bool) -> list[SearchHit]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chapter = path.stem if domain == "chapters" else ""
        rel = path.relative_to(self.project_root)
        hits: list[SearchHit] = []
        for index, raw_line in enumerate(text.splitlines(), start=1):
            haystack = raw_line if exact else raw_line.casefold()
            if needle in haystack:
                hits.append(
                    SearchHit(
                        domain=domain,
                        chapter=chapter,
                        path=str(rel),
                        line=index,
                        snippet=raw_line.strip(),
                    )
                )
        return hits


__all__ = ["SEARCH_SCOPES", "ManuscriptSearch", "SearchHit", "SearchResult"]
