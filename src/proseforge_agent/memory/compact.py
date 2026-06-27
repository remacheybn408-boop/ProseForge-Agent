"""Compact duplicate memory without losing sources or hiding contradictions.

Items whose text is identical (after normalization) are merged into a single
summary item that links back to every source id; the originals are marked
superseded so the active view collapses. Items with differing text are never
merged, so contradictions remain visible as separate active facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .store import MemoryItem, MemoryStore


@dataclass(frozen=True)
class CompactionReport:
    """What a compaction run merged, excluded, and produced."""

    included_ids: list[int] = field(default_factory=list)
    excluded_ids: list[int] = field(default_factory=list)
    summary_id: int | None = None
    summary_ids: list[int] = field(default_factory=list)
    source_coverage: list[int] = field(default_factory=list)


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


class MemoryCompactor:
    """Merge duplicate active memory items into auditable summaries."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def compact(self, project_slug: str, *, dry_run: bool = False) -> CompactionReport:
        items = self._store.list(project_slug=project_slug, status="active")

        groups: dict[str, list[MemoryItem]] = {}
        for item in items:
            groups.setdefault(_normalize(item.text), []).append(item)

        duplicate_groups = [g for g in groups.values() if len(g) > 1]
        included_ids = [item.id for group in duplicate_groups for item in group]
        included_set = set(included_ids)
        excluded_ids = [item.id for item in items if item.id not in included_set]

        if dry_run or not duplicate_groups:
            return CompactionReport(
                included_ids=included_ids,
                excluded_ids=excluded_ids,
                summary_id=None,
                summary_ids=[],
                source_coverage=[],
            )

        summary_ids: list[int] = []
        coverage: list[int] = []
        for group in duplicate_groups:
            member_ids = [item.id for item in group]
            representative = group[0]
            summary = self._store.add(
                MemoryItem(
                    project_slug=project_slug,
                    type=representative.type,
                    text=f"{representative.text} (merged from {len(group)} sources)",
                    source="compaction:" + ",".join(str(i) for i in member_ids),
                    confidence=representative.confidence,
                    tags=list(representative.tags),
                )
            )
            summary_ids.append(summary.id)
            coverage.extend(member_ids)
            for member_id in member_ids:
                self._store.mark_superseded(member_id)

        return CompactionReport(
            included_ids=included_ids,
            excluded_ids=excluded_ids,
            summary_id=summary_ids[0] if summary_ids else None,
            summary_ids=summary_ids,
            source_coverage=coverage,
        )


__all__ = ["CompactionReport", "MemoryCompactor"]
