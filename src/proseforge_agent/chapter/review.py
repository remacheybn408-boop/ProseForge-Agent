"""Editorial review of a chapter draft against professional gates.

A review scores nine categories (continuity, plot logic, character motivation,
pacing, prose quality, hook strength, promise handling, market fit, risk flags)
and separates objective continuity errors from taste-level suggestions. The
reviewer asks the critic-role provider for an opinion, but because the offline
fake provider returns unstructured text, gate scoring falls back to a
deterministic evaluation so the review output is always complete and repairable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.base import LLMProvider, Message, ProviderRequest
from .context import ChapterContextPackage
from .draft import ChapterDraft

REVIEW_CATEGORIES: tuple[str, ...] = (
    "continuity",
    "plot_logic",
    "character_motivation",
    "pacing",
    "prose_quality",
    "hook_strength",
    "promise_handling",
    "market_fit",
    "risk_flags",
)

# Categories whose failures are objective errors rather than taste suggestions.
OBJECTIVE: frozenset[str] = frozenset(
    {"continuity", "plot_logic", "promise_handling", "character_motivation", "risk_flags"}
)

_CRITIC_ROLE = "critic"


@dataclass
class ReviewFinding:
    """One reviewable issue, objective error or taste suggestion."""

    id: str
    category: str
    severity: str  # "info" | "warning" | "error"
    detail: str
    citation: str
    is_objective: bool


@dataclass
class ReviewReport:
    """Gate results, findings, citations, and an accept/revise recommendation."""

    chapter_no: int
    findings: list[ReviewFinding] = field(default_factory=list)
    gates: dict[str, str] = field(default_factory=dict)
    citations: list[str] = field(default_factory=list)
    recommendation: str = "accept"


@dataclass
class ReviewedChapter:
    """A draft bundled with its context and review for rewrite/accept stages."""

    project_slug: str
    chapter_no: int
    draft: ChapterDraft
    context: ChapterContextPackage
    review: ReviewReport


class ReviewPromptBuilder:
    """Build the critic-role review prompt from a draft and its context."""

    def build(self, draft: ChapterDraft, context: ChapterContextPackage) -> list[Message]:
        system = (
            "You are a professional novel editor. Score each category as "
            "pass/warning/fail. Separate OBJECTIVE continuity/plot errors from "
            "TASTE suggestions, and cite the scene or section for each finding."
        )
        beats = "\n".join(f"- {b}" for b in context.scene_beats) or "- (none)"
        user = (
            f"Chapter {context.chapter_no}, target {context.target_length} words.\n"
            f"Scene beats:\n{beats}\n"
            f"Manuscript word count: {draft.word_count}\n"
            f"Used evidence: {', '.join(draft.used_evidence) or '(none)'}\n"
            "Return your review."
        )
        return [Message(role="system", content=system), Message(role="user", content=user)]


class ChapterReviewer:
    """Evaluate a chapter draft and produce a gated review report."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._prompt = ReviewPromptBuilder()

    def review(self, draft: ChapterDraft, context: ChapterContextPackage) -> ReviewReport:
        # Ask the critic for an opinion (kept for parity / future structured
        # parsing); fake output is unstructured, so gates are scored
        # deterministically below — this is the review-output repair path.
        self._provider.generate(
            ProviderRequest(role=_CRITIC_ROLE, messages=self._prompt.build(draft, context))
        )

        gates = {category: "pass" for category in REVIEW_CATEGORIES}
        if not draft.used_evidence:
            gates["continuity"] = "fail"
        if draft.word_count < context.target_length:
            gates["prose_quality"] = "warning"

        default_citation = draft.scene_summaries[0] if draft.scene_summaries else (
            f"chapter:{context.chapter_no}"
        )
        findings: list[ReviewFinding] = []
        for category, status in gates.items():
            if status == "pass":
                continue
            findings.append(
                ReviewFinding(
                    id=f"{category}:{context.chapter_no}",
                    category=category,
                    severity="error" if status == "fail" else "warning",
                    detail=self._detail(category, status),
                    citation=default_citation,
                    is_objective=category in OBJECTIVE,
                )
            )

        recommendation = (
            "needs_revision" if any(s == "fail" for s in gates.values()) else "accept"
        )
        citations = [f.citation for f in findings] + list(draft.used_evidence)

        return ReviewReport(
            chapter_no=context.chapter_no,
            findings=findings,
            gates=gates,
            citations=citations,
            recommendation=recommendation,
        )

    @staticmethod
    def _detail(category: str, status: str) -> str:
        if category == "continuity" and status == "fail":
            return "draft cites no canon evidence; continuity unverifiable"
        if category == "prose_quality" and status == "warning":
            return "manuscript is shorter than the target length"
        return f"{category} flagged as {status}"


__all__ = [
    "REVIEW_CATEGORIES",
    "OBJECTIVE",
    "ReviewFinding",
    "ReviewReport",
    "ReviewedChapter",
    "ReviewPromptBuilder",
    "ChapterReviewer",
]
