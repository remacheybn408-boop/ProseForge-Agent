"""Review and ingest memory candidates into the store.

Candidates carry a proposed status; only accepted candidates are written to the
store. A dry run plans the work and writes nothing, so a reviewer can preview
what would be ingested.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..errors import MemoryError
from .ingest import IngestionCandidate
from .store import MemoryItem, MemoryStore


@dataclass
class IngestResult:
    """Outcome of an ingestion run."""

    created: list[MemoryItem] = field(default_factory=list)
    planned: int = 0
    dry_run: bool = False


def decide(candidate: IngestionCandidate, *, accepted: bool) -> IngestionCandidate:
    """Return a copy of the candidate with an accepted/rejected status."""
    return replace(candidate, status="accepted" if accepted else "rejected")


def _is_accepted(candidate: IngestionCandidate) -> bool:
    # Candidates are accepted unless they were explicitly rejected.
    return candidate.status != "rejected"


def ingest_candidates(
    store: MemoryStore,
    candidates: list[IngestionCandidate],
    *,
    dry_run: bool = True,
) -> IngestResult:
    """Write accepted candidates to the store, or plan the work on a dry run."""
    accepted = [c for c in candidates if _is_accepted(c)]
    for candidate in accepted:
        if not candidate.source_path or not candidate.reason:
            raise MemoryError("candidate is missing a source path or reason")

    if dry_run:
        return IngestResult(created=[], planned=len(accepted), dry_run=True)

    created: list[MemoryItem] = []
    for candidate in accepted:
        item = store.add(
            MemoryItem(
                project_slug=candidate.project_slug,
                type=candidate.proposed_type,
                text=candidate.extracted_text,
                source=f"{candidate.source_kind}:{candidate.source_path}",
                confidence=candidate.confidence,
            )
        )
        created.append(item)
    return IngestResult(created=created, planned=len(accepted), dry_run=False)


__all__ = ["IngestResult", "decide", "ingest_candidates"]
