"""Targeted rewrite planning and execution.

A rewrite plan turns failing review gates into prioritized, individually
verifiable rewrite items — high-priority continuity fixes outrank prose polish,
and taste-level warnings are deferred rather than forced into a full
regeneration. Execution applies the plan through the reviser-role provider while
preserving the source manuscript and emitting a change summary, so a failed
revision never silently overwrites the prior draft.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.base import LLMProvider, Message, ProviderRequest
from .context import ChapterContextPackage, ChapterWorkflowError
from .draft import ChapterDraft
from .review import ReviewReport

_REVISER_ROLE = "reviser"

# Lower number = higher priority. Continuity/plot/promise outrank prose polish.
_PRIORITY: dict[str, int] = {
    "continuity": 1,
    "plot_logic": 1,
    "promise_handling": 1,
    "character_motivation": 1,
    "risk_flags": 1,
    "pacing": 2,
    "hook_strength": 2,
    "prose_quality": 3,
    "market_fit": 3,
}


@dataclass
class RewriteItem:
    """One targeted change with its own acceptance criteria."""

    issue_id: str
    priority: int
    affected_scene: str
    proposed_change: str
    memory_references: list[str] = field(default_factory=list)
    risk: str = ""
    acceptance_criteria: str = ""


@dataclass
class RewritePlan:
    """A prioritized set of targeted rewrites plus deferred suggestions."""

    chapter_no: int
    items: list[RewriteItem] = field(default_factory=list)
    deferred: list[RewriteItem] = field(default_factory=list)
    source_draft_ref: str = ""


@dataclass
class RevisedDraft:
    """A revised manuscript that preserves the source and summarizes changes."""

    manuscript: str
    source_manuscript: str
    change_summary: list[str] = field(default_factory=list)
    used_evidence: list[str] = field(default_factory=list)
    applied_items: list[str] = field(default_factory=list)


def _priority(category: str) -> int:
    return _PRIORITY.get(category, 2)


class RewritePlanner:
    """Build a targeted rewrite plan from a review report."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def plan(self, review: ReviewReport, context: ChapterContextPackage) -> RewritePlan:
        items: list[RewriteItem] = []
        deferred: list[RewriteItem] = []
        for finding in review.findings:
            item = RewriteItem(
                issue_id=f"{finding.category}:{review.chapter_no}",
                priority=_priority(finding.category),
                affected_scene=finding.citation,
                proposed_change=f"Address {finding.category}: {finding.detail}",
                memory_references=list(context.source_references),
                risk=finding.detail,
                acceptance_criteria=f"{finding.category} gate passes on re-review",
            )
            # Objective failures become active fixes; taste warnings are deferred
            # (targeted rewrite, not a full regeneration by default).
            if finding.severity == "error":
                items.append(item)
            else:
                deferred.append(item)
        items.sort(key=lambda i: i.priority)
        return RewritePlan(
            chapter_no=review.chapter_no,
            items=items,
            deferred=deferred,
            source_draft_ref=f"chapter:{review.chapter_no}:draft",
        )


class RewritePromptBuilder:
    """Build the reviser-role rewrite prompt with exact items and evidence."""

    def build(
        self, plan: RewritePlan, draft: ChapterDraft, context: ChapterContextPackage
    ) -> list[Message]:
        system = (
            "You are a novel reviser. Apply ONLY the listed rewrite items. "
            "Preserve unchanged scenes. Honor canon evidence."
        )
        items = "\n".join(
            f"- [{item.issue_id}] {item.proposed_change} (accept: {item.acceptance_criteria})"
            for item in plan.items
        ) or "- (none)"
        evidence = ", ".join(context.source_references) or "(none)"
        user = (
            f"Chapter {plan.chapter_no} rewrite.\n"
            f"Rewrite items:\n{items}\n"
            f"Evidence: {evidence}\n"
            f"Current manuscript words: {draft.word_count}\n"
            "Return the revised manuscript."
        )
        return [Message(role="system", content=system), Message(role="user", content=user)]


class Rewriter:
    """Apply a rewrite plan through the reviser provider, preserving the source."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._prompt = RewritePromptBuilder()

    def apply(
        self, plan: RewritePlan, draft: ChapterDraft, context: ChapterContextPackage
    ) -> RevisedDraft:
        result = self._provider.generate(
            ProviderRequest(
                role=_REVISER_ROLE, messages=self._prompt.build(plan, draft, context)
            )
        )
        applied = [item.issue_id for item in plan.items]
        change_summary = [
            f"applied {item.issue_id}: {item.proposed_change}" for item in plan.items
        ] or ["no targeted changes required"]
        return RevisedDraft(
            manuscript=result.text,
            source_manuscript=draft.manuscript,
            change_summary=change_summary,
            used_evidence=list(draft.used_evidence),
            applied_items=applied,
        )


class RevisionValidator:
    """Reject an empty revision or one without a change summary."""

    def validate(self, revised: RevisedDraft, plan: RewritePlan) -> list[str]:
        problems: list[str] = []
        if not revised.manuscript.strip():
            problems.append("revised manuscript is empty")
        if not revised.change_summary:
            problems.append("revision has no change summary")
        return problems

    def validate_or_raise(self, revised: RevisedDraft, plan: RewritePlan) -> RevisedDraft:
        problems = self.validate(revised, plan)
        if problems:
            raise ChapterWorkflowError("invalid revision: " + "; ".join(problems))
        return revised


__all__ = [
    "RewriteItem",
    "RewritePlan",
    "RevisedDraft",
    "RewritePlanner",
    "RewritePromptBuilder",
    "Rewriter",
    "RevisionValidator",
]
