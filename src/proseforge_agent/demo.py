"""End-to-end demo runner: the full Agent spine on the fake provider.

The demo composes every subsystem built so far — provider routing, intake, phase
planning, daily workbook, chapter drafting, review, memory, and export dry-run —
into one offline, deterministic flow that writes a portable report pack. It uses
no real API key and bakes no machine-specific path into its output, so it
doubles as the release smoke test.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .chapter.lifecycle import ChapterLifecycle, ChapterProject
from .chapter.review import ChapterReviewer
from .daily.recommend import ProjectState
from .daily.workbook import DailyWorkbookEngine
from .errors import ProseForgeAgentError
from .llm.base import Message, ProviderRequest
from .llm.registry import ProviderRegistry
from .memory.store import MemoryItem, MemoryStore
from .planning.intake import ProjectIntake, validate_intake
from .planning.phase_plan import PhasePlanGenerator
from .proseforge.adapter import ProseForgeAdapter
from .reports import Report, ReportRenderer, ReportSection

_DEMO_DATE = "2026-08-15"

_DEMO_INTAKE: dict = {
    "slug": "demo_novel",
    "title": "Demo Novel",
    "genre": "fantasy",
    "target_chapters": 12,
    "market": "serialized web fiction",
    "length": "long",
    "cadence": "daily",
    "tone": "冷峻",
    "audience": "成人向",
    "constraints": ["不得提前揭示反派身份", "保持第三人称限知视角"],
}

_DEMO_ROADMAP: dict = {
    "project_slug": "demo_novel",
    "chapters": [
        {
            "chapter_no": 1,
            "title": "启程",
            "target_length": 2000,
            "scene_beats": ["主角接到密信", "雨夜离城"],
            "constraints": ["不得提前揭示反派身份"],
            "gates": ["建立主角动机", "埋下密信伏笔"],
            "previous_summary": "",
        }
    ],
}

_REGISTRY_DATA = {
    "providers": [{"name": "fake", "kind": "fake", "model": "fake-1"}],
    "roles": {"drafter": "fake", "planner": "fake", "critic": "fake"},
    "default_provider": "fake",
}


class DemoError(ProseForgeAgentError):
    """Raised when the demo flow cannot complete."""


@dataclass
class DemoResult:
    """Paths to every artifact the demo produced."""

    status: str
    provider: str
    provider_certified: bool
    intake: Path
    phase_plan: Path
    daily_workbook: Path
    chapter_context: Path
    chapter_draft: Path
    review_report: Path
    export_report: Path
    memory_candidates: Path
    closeout: Path
    report_pack: Path


class DemoRunner:
    """Run the full fake-provider demo under a root directory."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def run(self, provider: str = "fake") -> DemoResult:
        from .workspace import WorkspaceLayout

        workspace = WorkspaceLayout(self._root / "workspace").ensure()
        out = workspace.reports

        registry = ProviderRegistry.from_dict(_REGISTRY_DATA)
        prov = registry.provider_for_role("drafter")

        certified = self._certify(prov)
        cert_path = out / "provider-certification.md"
        cert_path.write_text(
            f"# Provider Certification\n\n- provider: {prov.name}\n"
            f"- deterministic: {certified}\n",
            encoding="utf-8",
        )
        if not certified:
            raise DemoError("fake provider failed deterministic certification")

        intake = ProjectIntake(**_DEMO_INTAKE)
        validate_intake(intake)
        intake_path = out / "intake.yaml"
        intake_path.write_text(
            yaml.safe_dump(_DEMO_INTAKE, allow_unicode=True, sort_keys=True),
            encoding="utf-8",
        )

        store = MemoryStore(workspace.agent_db)
        try:
            return self._build(
                workspace, out, registry, prov, certified, cert_path, store, intake, intake_path
            )
        finally:
            store.close()

    def _build(
        self, workspace, out, registry, prov, certified, cert_path, store, intake, intake_path
    ) -> DemoResult:
        self._seed_memory(store)

        plan = PhasePlanGenerator(prov, store).generate(intake)
        phase_plan_path = out / "phase-plan.md"
        phase_plan_path.write_text(
            PhasePlanGenerator(prov, store).render_markdown(plan), encoding="utf-8"
        )

        state = ProjectState(
            slug=intake.slug,
            target_chapters=intake.target_chapters,
            completed_chapters=0,
            current_chapter=1,
        )
        engine = DailyWorkbookEngine()
        workbook = engine.generate(state, date=_DEMO_DATE)
        daily_path = out / "daily-workbook.md"
        daily_path.write_text(engine.render_markdown(workbook), encoding="utf-8")

        project = ChapterProject(
            slug=intake.slug,
            workspace=workspace,
            store=store,
            registry=registry,
            roadmap=_DEMO_ROADMAP,
        )
        chapter_run = ChapterLifecycle(project).run(
            chapter_no=1, provider_name="fake", until="draft"
        )

        review = ChapterReviewer(prov).review(chapter_run.draft, chapter_run.context)
        review_path = out / "review-report.md"
        review_path.write_text(self._render_review(review), encoding="utf-8")

        export = ProseForgeAdapter(workspace.workspace_root).run_pipeline_action(
            "export", dry_run=True
        )
        export_path = out / "export-dry-run.md"
        export_path.write_text(
            f"# Export Dry-Run\n\n- status: {export.status}\n"
            f"- command: {' '.join(Path(part).name if i == 1 else part for i, part in enumerate(export.command))}\n",
            encoding="utf-8",
        )

        candidates = [f"chapter:1 summary", *chapter_run.context.source_references]
        candidates_path = out / "memory-candidates.md"
        candidates_path.write_text(
            "# Memory Update Candidates\n\n"
            + "\n".join(f"- {c}" for c in candidates),
            encoding="utf-8",
        )

        closeout_path = out / "closeout.md"
        closeout_path.write_text(
            "# Demo Closeout\n\n- chapter 1 drafted and reviewed\n"
            f"- review recommendation: {review.recommendation}\n",
            encoding="utf-8",
        )

        artifacts = {
            "intake": intake_path,
            "phase-plan": phase_plan_path,
            "daily-workbook": daily_path,
            "chapter-context": chapter_run.artifacts.context_path,
            "chapter-draft": chapter_run.artifacts.draft_path,
            "review-report": review_path,
            "export-dry-run": export_path,
            "memory-candidates": candidates_path,
            "closeout": closeout_path,
            "provider-certification": cert_path,
        }
        report_pack_path = self._write_report_pack(out, artifacts)

        return DemoResult(
            status="ok",
            provider="fake",
            provider_certified=certified,
            intake=intake_path,
            phase_plan=phase_plan_path,
            daily_workbook=daily_path,
            chapter_context=chapter_run.artifacts.context_path,
            chapter_draft=chapter_run.artifacts.draft_path,
            review_report=review_path,
            export_report=export_path,
            memory_candidates=candidates_path,
            closeout=closeout_path,
            report_pack=report_pack_path,
        )

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _certify(provider) -> bool:
        request = ProviderRequest(
            role="drafter",
            messages=[Message(role="user", content="certify deterministic output")],
        )
        first = provider.generate(request).text
        second = provider.generate(request).text
        return first == second and bool(first)

    @staticmethod
    def _seed_memory(store: MemoryStore) -> None:
        store.add(MemoryItem(project_slug="demo_novel", type="canon_fact", text="主角名叫林远", source="bible:canon"))
        store.add(MemoryItem(project_slug="demo_novel", type="style", text="第三人称冷峻文风", source="bible:style"))
        store.add(MemoryItem(project_slug="demo_novel", type="risk", text="勿提前揭示反派", source="bible:risk"))

    @staticmethod
    def _render_review(review) -> str:
        lines = [
            "# Chapter Review",
            f"- recommendation: {review.recommendation}",
            "",
            "## Gates",
        ]
        lines += [f"- {name}: {status}" for name, status in review.gates.items()]
        return "\n".join(lines) + "\n"

    def _write_report_pack(self, out: Path, artifacts: dict[str, Path]) -> Path:
        sections = [
            ReportSection(
                heading="Artifacts",
                lines=[
                    f"{name}: {path.relative_to(self._root).as_posix()}"
                    for name, path in artifacts.items()
                ],
            )
        ]
        report = Report(
            title="ProseForge Agent Demo — Report Pack",
            status="ok",
            next_action="Review the artifacts, then run `pf-agent` against a real project",
            sections=sections,
            data={"provider": "fake", "date": _DEMO_DATE},
        )
        path = out / "report-pack.md"
        path.write_text(ReportRenderer().render(report, "markdown"), encoding="utf-8")
        return path


def run_demo(root: str | Path, provider: str = "fake") -> DemoResult:
    """Convenience wrapper for callers and manual verification."""
    return DemoRunner(root).run(provider=provider)


__all__ = ["DemoError", "DemoResult", "DemoRunner", "run_demo"]
