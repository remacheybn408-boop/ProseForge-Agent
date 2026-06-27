"""Chapter context package: the brief the drafter receives before writing.

A context package gathers everything a drafter needs — the roadmap entry,
retrieved evidence, the previous chapter summary, target length, scene beats,
constraints, and acceptance gates — and cites every evidence source. A draft is
never produced without an evidence pack: if memory yields nothing, the package
carries a ``blocked_reason`` so the lifecycle stops with a clear explanation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..errors import ProseForgeAgentError
from ..retrieval.evidence import EvidencePack, EvidencePackBuilder

# Mapped in retrieval.router.INTENT_QUERY_TERMS; selects canon/promise/setting.
_DRAFT_INTENT = "chapter_draft"


class ChapterWorkflowError(ProseForgeAgentError):
    """Raised when a chapter cannot be prepared, drafted, or advanced."""


@dataclass
class ChapterContextPackage:
    """A complete drafting brief for one chapter."""

    project_slug: str
    chapter_no: int
    roadmap_entry: dict
    evidence_pack: EvidencePack
    previous_summary: str = ""
    target_length: int = 0
    scene_beats: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    source_references: list[str] = field(default_factory=list)
    blocked_reason: str = ""


def _roadmap_entry(roadmap: dict, chapter_no: int) -> dict | None:
    for entry in roadmap.get("chapters", []):
        if entry.get("chapter_no") == chapter_no:
            return entry
    return None


class ChapterContextBuilder:
    """Assemble a cited, evidence-backed drafting brief for a chapter."""

    def __init__(self, evidence_builder: EvidencePackBuilder) -> None:
        self._evidence = evidence_builder

    def build(
        self,
        roadmap: dict,
        slug: str,
        chapter_no: int,
        *,
        token_budget: int = 1200,
    ) -> ChapterContextPackage:
        entry = _roadmap_entry(roadmap, chapter_no)
        if entry is None:
            raise ChapterWorkflowError(f"roadmap has no chapter {chapter_no}")

        pack = self._evidence.build(
            slug, _DRAFT_INTENT, chapter_no=chapter_no, token_budget=token_budget
        )
        blocked_reason = ""
        if pack.degraded_reason:
            blocked_reason = f"no evidence pack available: {pack.degraded_reason}"

        references = [f"roadmap:chapter:{chapter_no}"]
        for item in pack.items:
            if item.source not in references:
                references.append(item.source)

        return ChapterContextPackage(
            project_slug=slug,
            chapter_no=chapter_no,
            roadmap_entry=entry,
            evidence_pack=pack,
            previous_summary=entry.get("previous_summary", ""),
            target_length=int(entry.get("target_length", 0)),
            scene_beats=list(entry.get("scene_beats", [])),
            constraints=list(entry.get("constraints", [])),
            gates=list(entry.get("gates", [])),
            source_references=references,
            blocked_reason=blocked_reason,
        )

    def render_markdown(self, context: ChapterContextPackage) -> str:
        entry = context.roadmap_entry
        lines = [
            f"# Chapter {context.chapter_no} Context — {entry.get('title', '')}",
            f"_target length: {context.target_length} words_",
            "",
            "## Previous Summary",
            context.previous_summary or "_(none)_",
            "",
            "## Scene Beats",
        ]
        lines += [f"- {beat}" for beat in context.scene_beats] or ["_(none)_"]
        lines += ["", "## Constraints"]
        lines += [f"- {c}" for c in context.constraints] or ["_(none)_"]
        lines += ["", "## Acceptance Gates"]
        lines += [f"- {g}" for g in context.gates] or ["_(none)_"]
        lines += ["", self._evidence.render_markdown(context.evidence_pack)]
        return "\n".join(lines)


__all__ = ["ChapterWorkflowError", "ChapterContextPackage", "ChapterContextBuilder"]
