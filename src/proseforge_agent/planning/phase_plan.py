"""Structured phase plan generation.

The structural skeleton — volume arcs, contiguous chapter ranges, acceptance
gates, and deliverables — is computed deterministically, so a usable plan is
produced even without any model call. An injected provider may enrich volume
themes; if its output cannot be parsed it is rejected and a parse report
records why, while the deterministic plan stands.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..llm.base import LLMProvider, Message, ProviderRequest
from ..memory.store import MemoryStore
from .intake import ProjectIntake, validate_intake

_DEFAULT_CHAPTERS_PER_VOLUME = 12

_GLOBAL_GATES = (
    "Canon consistency verified against memory",
    "Reader promises tracked and paid off",
    "Pacing matches the configured cadence",
)


@dataclass(frozen=True)
class VolumeArc:
    """One volume's arc and chapter span."""

    volume_no: int
    title: str
    chapter_start: int
    chapter_end: int
    theme: str
    deliverables: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParseReport:
    """Whether the provider's enrichment output was usable."""

    ok: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class PhasePlan:
    """A machine-checkable phase plan for a novel project."""

    slug: str
    title: str
    genre: str
    target_chapters: int
    volumes: list[VolumeArc]
    acceptance_gates: list[str]
    deliverables: list[str]
    source_references: list[str]
    parse_report: ParseReport


class PlannerPromptBuilder:
    """Build the planner-role prompt from intake and memory evidence."""

    def build(self, intake: ProjectIntake, evidence_lines: list[str]) -> list[Message]:
        system = (
            "You are a novel structure planner. Return a JSON object with a "
            "'volumes' array; each item may include a 'theme' string."
        )
        evidence = "\n".join(f"- {line}" for line in evidence_lines) or "- (none)"
        user = (
            f"Title: {intake.title}\nGenre: {intake.genre}\n"
            f"Target chapters: {intake.target_chapters}\n"
            f"Tone: {intake.tone}\nAudience: {intake.audience}\n"
            f"Memory evidence:\n{evidence}"
        )
        return [Message(role="system", content=system), Message(role="user", content=user)]


def _build_volumes(target_chapters: int, per_volume: int) -> list[VolumeArc]:
    volumes: list[VolumeArc] = []
    start = 1
    volume_no = 1
    while start <= target_chapters:
        end = min(start + per_volume - 1, target_chapters)
        volumes.append(
            VolumeArc(
                volume_no=volume_no,
                title=f"Volume {volume_no}",
                chapter_start=start,
                chapter_end=end,
                theme=f"Volume {volume_no} arc",
                deliverables=[
                    f"Draft chapters {start}-{end}",
                    f"Volume {volume_no} continuity pass",
                ],
                gates=[f"Volume {volume_no} arc resolved"],
            )
        )
        start = end + 1
        volume_no += 1
    return volumes


class PhasePlanGenerator:
    """Generate a structured phase plan from intake and memory."""

    def __init__(
        self,
        provider: LLMProvider,
        store: MemoryStore,
        *,
        chapters_per_volume: int = _DEFAULT_CHAPTERS_PER_VOLUME,
    ) -> None:
        self._provider = provider
        self._store = store
        self._per_volume = chapters_per_volume
        self._prompt_builder = PlannerPromptBuilder()

    def generate(self, intake: ProjectIntake) -> PhasePlan:
        validate_intake(intake)

        volumes = _build_volumes(intake.target_chapters, self._per_volume)
        source_references = self._collect_sources(intake)

        themes, report = self._enrich_themes(intake, source_references)
        if themes:
            volumes = self._apply_themes(volumes, themes)

        acceptance_gates = [g for v in volumes for g in v.gates] + list(_GLOBAL_GATES)
        deliverables = [d for v in volumes for d in v.deliverables]

        return PhasePlan(
            slug=intake.slug,
            title=intake.title,
            genre=intake.genre,
            target_chapters=intake.target_chapters,
            volumes=volumes,
            acceptance_gates=acceptance_gates,
            deliverables=deliverables,
            source_references=source_references,
            parse_report=report,
        )

    def _collect_sources(self, intake: ProjectIntake) -> list[str]:
        refs = [f"intake:{intake.slug}"]
        for item in self._store.list(project_slug=intake.slug):
            if item.source not in refs:
                refs.append(item.source)
        return refs

    def _enrich_themes(
        self, intake: ProjectIntake, source_references: list[str]
    ) -> tuple[list[str], ParseReport]:
        messages = self._prompt_builder.build(intake, source_references)
        result = self._provider.generate(
            ProviderRequest(role="planner", messages=messages)
        )
        try:
            payload = json.loads(result.text)
            entries = payload["volumes"]
            themes = [str(entry.get("theme", "")) for entry in entries]
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
            return [], ParseReport(
                ok=False,
                reasons=[f"planner output was not a valid plan payload: {exc}"],
            )
        return themes, ParseReport(ok=True)

    @staticmethod
    def _apply_themes(volumes: list[VolumeArc], themes: list[str]) -> list[VolumeArc]:
        updated: list[VolumeArc] = []
        for index, volume in enumerate(volumes):
            theme = themes[index] if index < len(themes) and themes[index] else volume.theme
            updated.append(
                VolumeArc(
                    volume_no=volume.volume_no,
                    title=volume.title,
                    chapter_start=volume.chapter_start,
                    chapter_end=volume.chapter_end,
                    theme=theme,
                    deliverables=volume.deliverables,
                    gates=volume.gates,
                )
            )
        return updated

    def render_markdown(self, plan: PhasePlan) -> str:
        lines = [f"# Phase Plan — {plan.title} ({plan.genre})", ""]
        for volume in plan.volumes:
            lines.append(
                f"## {volume.title}: chapters {volume.chapter_start}-{volume.chapter_end}"
            )
            lines.append(f"_Theme: {volume.theme}_")
            for deliverable in volume.deliverables:
                lines.append(f"- {deliverable}")
            lines.append("")
        lines.append("## Acceptance Gates")
        for gate in plan.acceptance_gates:
            lines.append(f"- {gate}")
        lines.append("")
        lines.append("## Source References")
        for ref in plan.source_references:
            lines.append(f"- {ref}")
        return "\n".join(lines)


__all__ = ["VolumeArc", "ParseReport", "PhasePlan", "PlannerPromptBuilder", "PhasePlanGenerator"]
