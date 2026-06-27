"""Chapter acceptance: lock final text as project state, with audit gates.

Acceptance is an editorial decision, not a derived value. Failed review gates
block normal acceptance; they can only be overridden by an explicit force-accept
that records a human-readable audit reason. An accepted record is frozen — the
locked text is immutable unless a new accepted version supersedes it — and it
carries the memory-update candidates that the accepted chapter generates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..errors import ProseForgeAgentError
from .review import ReviewedChapter


class AcceptanceError(ProseForgeAgentError):
    """Raised when a chapter cannot be accepted under the audit rules."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AcceptanceRecord:
    """An immutable record of an accepted chapter."""

    project_slug: str
    chapter_no: int
    final_text: str
    reason: str
    gate_status: dict = field(default_factory=dict)
    forced: bool = False
    accepted_at: str = ""
    memory_update_candidates: tuple[str, ...] = ()
    human_approved: bool = False


class ChapterAcceptor:
    """Accept a chapter, enforcing gate and audit rules."""

    def accept(
        self,
        run: ReviewedChapter,
        *,
        force: bool = False,
        reason: str = "",
        human_approved: bool = False,
    ) -> AcceptanceRecord:
        failed = [name for name, status in run.review.gates.items() if status == "fail"]

        if failed and not force:
            raise AcceptanceError(
                f"failed gates {failed}: correct them or force-accept with an audit reason"
            )
        if failed and force and not reason.strip():
            raise AcceptanceError(
                "force-accept of failed gates requires an audit reason"
            )

        candidates = (
            f"chapter:{run.chapter_no} summary",
            *run.context.source_references,
        )
        return AcceptanceRecord(
            project_slug=run.project_slug,
            chapter_no=run.chapter_no,
            final_text=run.draft.manuscript,
            reason=reason,
            gate_status=dict(run.review.gates),
            forced=bool(failed),
            accepted_at=_now(),
            memory_update_candidates=candidates,
            human_approved=human_approved,
        )


__all__ = ["AcceptanceError", "AcceptanceRecord", "ChapterAcceptor"]
