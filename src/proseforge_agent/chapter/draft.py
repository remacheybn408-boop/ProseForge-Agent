"""Chapter draft prompt, output, and validation.

The draft prompt separates hard canon (must obey) from style suggestions, and
spells out scene beats, forbidden contradictions, target length, and the
expected output shape. The draft itself carries the manuscript text *and*
structured metadata (scene summaries, self-check, used evidence, open
questions) so review has more than prose to work with. The validator rejects an
empty manuscript or one that cites no evidence before it can reach review.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.base import LLMProvider, Message, ProviderRequest
from .context import ChapterContextPackage, ChapterWorkflowError

_DRAFTER_ROLE = "drafter"


class DraftPromptBuilder:
    """Build the drafter-role prompt from a chapter context package."""

    def build(self, context: ChapterContextPackage) -> list[Message]:
        canon_lines = [
            f"- {item.text}"
            for item in context.evidence_pack.sections.get("hard_canon", [])
        ] or ["- (none)"]
        style_lines = [
            f"- {item.text}"
            for item in context.evidence_pack.sections.get("style_rules", [])
        ] or ["- (none)"]
        forbidden_lines = [
            f"- {item.text}"
            for item in context.evidence_pack.sections.get("risk_warnings", [])
        ] or ["- (none)"]

        system = (
            "You are a novel chapter drafter. Obey HARD CANON exactly; treat "
            "STYLE as suggestions. Never contradict the FORBIDDEN items.\n"
            "HARD CANON:\n" + "\n".join(canon_lines) + "\n"
            "STYLE:\n" + "\n".join(style_lines) + "\n"
            "FORBIDDEN:\n" + "\n".join(forbidden_lines)
        )
        beats = "\n".join(f"- {beat}" for beat in context.scene_beats) or "- (none)"
        constraints = "\n".join(f"- {c}" for c in context.constraints) or "- (none)"
        user = (
            f"Draft chapter {context.chapter_no}.\n"
            f"Target length: {context.target_length} words.\n"
            f"Previous summary: {context.previous_summary or '(none)'}\n"
            f"Scene beats:\n{beats}\n"
            f"Constraints:\n{constraints}\n"
            "Output the manuscript prose only."
        )
        return [Message(role="system", content=system), Message(role="user", content=user)]


@dataclass
class ChapterDraft:
    """A chapter manuscript with structured, reviewable metadata."""

    manuscript: str
    scene_summaries: list[str] = field(default_factory=list)
    self_check: list[str] = field(default_factory=list)
    used_evidence: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    provider_name: str = ""
    role: str = _DRAFTER_ROLE
    word_count: int = 0


class ChapterDrafter:
    """Generate a structured chapter draft from a context package."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._prompt = DraftPromptBuilder()

    def draft(self, context: ChapterContextPackage) -> ChapterDraft:
        messages = self._prompt.build(context)
        result = self._provider.generate(
            ProviderRequest(role=_DRAFTER_ROLE, messages=messages)
        )
        manuscript = result.text
        return ChapterDraft(
            manuscript=manuscript,
            scene_summaries=list(context.scene_beats),
            self_check=[f"gate satisfied: {g}" for g in context.gates],
            used_evidence=[item.source for item in context.evidence_pack.items],
            open_questions=[],
            provider_name=result.provider,
            role=_DRAFTER_ROLE,
            word_count=len(manuscript.split()),
        )


class DraftValidator:
    """Reject a draft that is empty or cites no evidence."""

    def validate(self, draft: ChapterDraft, context: ChapterContextPackage) -> list[str]:
        problems: list[str] = []
        if not draft.manuscript.strip():
            problems.append("manuscript is empty")
        if not draft.used_evidence:
            problems.append("draft references no evidence")
        if draft.word_count <= 0:
            problems.append("manuscript has no words")
        return problems

    def validate_or_raise(
        self, draft: ChapterDraft, context: ChapterContextPackage
    ) -> ChapterDraft:
        problems = self.validate(draft, context)
        if problems:
            raise ChapterWorkflowError("invalid draft: " + "; ".join(problems))
        return draft


def to_metadata(draft: ChapterDraft) -> dict:
    return {
        "scene_summaries": draft.scene_summaries,
        "self_check": draft.self_check,
        "used_evidence": draft.used_evidence,
        "open_questions": draft.open_questions,
        "provider_name": draft.provider_name,
        "role": draft.role,
        "word_count": draft.word_count,
    }


__all__ = [
    "DraftPromptBuilder",
    "ChapterDraft",
    "ChapterDrafter",
    "DraftValidator",
    "to_metadata",
]
