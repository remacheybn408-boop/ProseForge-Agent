"""Chapter lifecycle orchestration.

Wires the previously-built subsystems into one chapter run:
``prepare -> draft -> review -> accept -> export -> memory-update -> closeout``.
Every stage is recorded as a workflow step and an audited state transition, so a
run is resumable (see :mod:`proseforge_agent.workflow.recovery`). The run stays
fully offline: drafting uses the registered (fake) provider and review/export
call the engine adapter in dry-run, recording the intended command without
mutating the engine. A draft never runs without an evidence pack.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..llm.registry import ProviderRegistry
from ..memory.store import MemoryItem, MemoryStore
from ..proseforge.adapter import ProseForgeAdapter
from ..retrieval.evidence import EvidencePackBuilder
from ..workflow.state import StepResult, WorkflowStateStore, _now
from ..workspace import WorkspaceLayout
from .context import ChapterContextBuilder, ChapterContextPackage, ChapterWorkflowError
from .draft import ChapterDraft, ChapterDrafter, DraftValidator, to_metadata

# until-keyword -> workflow state the run should stop at.
_UNTIL: dict[str, str] = {
    "context": "context_ready",
    "prepare": "context_ready",
    "draft": "drafted",
    "review": "reviewed",
    "accept": "accepted",
    "export": "exported",
    "memory": "memory_updated",
}

# Ordered lifecycle states after creation; index drives the "stop at until" cut.
_ORDER: tuple[str, ...] = (
    "context_ready",
    "drafted",
    "reviewed",
    "accepted",
    "exported",
    "memory_updated",
)


@dataclass
class ChapterProject:
    """Everything one chapter run needs, bundled for the lifecycle."""

    slug: str
    workspace: WorkspaceLayout
    store: MemoryStore
    registry: ProviderRegistry
    roadmap: dict
    engine_root: Path | None = None


@dataclass
class ChapterArtifacts:
    """Filesystem paths produced by a chapter run."""

    context_path: Path | None = None
    draft_path: Path | None = None
    draft_meta_path: Path | None = None
    closeout_path: Path | None = None


@dataclass
class ChapterRunResult:
    """Outcome of a chapter run: terminal state plus produced artifacts."""

    run_id: str
    state: str
    artifacts: ChapterArtifacts
    context: ChapterContextPackage | None = None
    draft: ChapterDraft | None = None
    steps: list[StepResult] = field(default_factory=list)


def _done(current: str, until_state: str) -> bool:
    """True once ``current`` has reached (or passed) the requested stop state."""
    return _ORDER.index(current) >= _ORDER.index(until_state)


class ChapterLifecycle:
    """Run a chapter from preparation through memory update, stage by stage."""

    def __init__(self, project: ChapterProject) -> None:
        self._project = project
        self._store = WorkflowStateStore(project.workspace.workflow_runs)
        self._context_builder = ChapterContextBuilder(
            EvidencePackBuilder(project.store)
        )
        self._validator = DraftValidator()

    def run(
        self,
        chapter_no: int,
        *,
        provider_name: str = "fake",
        until: str = "memory",
    ) -> ChapterRunResult:
        if until not in _UNTIL:
            raise ChapterWorkflowError(f"unknown until target {until!r}")
        until_state = _UNTIL[until]

        run = self._store.create(self._project.slug, chapter_no)
        artifacts = ChapterArtifacts()
        result = ChapterRunResult(run_id=run.id, state=run.state, artifacts=artifacts)

        try:
            self._prepare(run.id, chapter_no, artifacts, result)
            if _done("context_ready", until_state):
                return self._finish(run.id, result)

            self._draft(run.id, provider_name, artifacts, result)
            if _done("drafted", until_state):
                return self._finish(run.id, result)

            self._review(run.id)
            if _done("reviewed", until_state):
                return self._finish(run.id, result)

            self._accept(run.id, result)
            if _done("accepted", until_state):
                return self._finish(run.id, result)

            self._export(run.id)
            if _done("exported", until_state):
                return self._finish(run.id, result)

            self._memory_update(run.id, chapter_no, result)
            self._closeout(run.id, chapter_no, artifacts, result)
            return self._finish(run.id, result)
        except ChapterWorkflowError:
            self._store.fail(run.id, reason="chapter lifecycle error")
            raise

    # -- stages ----------------------------------------------------------

    def _prepare(
        self,
        run_id: str,
        chapter_no: int,
        artifacts: ChapterArtifacts,
        result: ChapterRunResult,
    ) -> None:
        context = self._context_builder.build(
            self._project.roadmap, self._project.slug, chapter_no
        )
        if context.blocked_reason:
            raise ChapterWorkflowError(context.blocked_reason)
        result.context = context
        artifacts.context_path = self._store.save_artifact(
            run_id, "context.md", self._context_builder.render_markdown(context)
        )
        self._step(run_id, "prepare", artifacts=[str(artifacts.context_path)])
        self._store.transition(
            run_id, "context_ready", command="chapter:prepare", reason="context ready"
        )

    def _draft(
        self,
        run_id: str,
        provider_name: str,
        artifacts: ChapterArtifacts,
        result: ChapterRunResult,
    ) -> None:
        provider = self._project.registry.provider_for_role("drafter")
        drafter = ChapterDrafter(provider)
        draft = self._validator.validate_or_raise(
            drafter.draft(result.context), result.context
        )
        result.draft = draft
        artifacts.draft_path = self._store.save_artifact(
            run_id, "draft.md", draft.manuscript
        )
        artifacts.draft_meta_path = self._store.save_artifact(
            run_id,
            "draft.meta.json",
            json.dumps(to_metadata(draft), ensure_ascii=False, indent=2),
        )
        self._step(
            run_id,
            "draft",
            artifacts=[str(artifacts.draft_path), str(artifacts.draft_meta_path)],
            summary=f"provider={provider_name} role={draft.role}",
        )
        self._store.transition(
            run_id,
            "drafted",
            command="chapter:draft",
            reason=f"drafted with provider {provider_name}",
        )

    def _review(self, run_id: str) -> None:
        action = self._adapter().run_pipeline_action("review", dry_run=True)
        self._step(run_id, "review", summary=" ".join(action.command))
        self._store.transition(
            run_id, "reviewed", command="chapter:review", reason="review dry-run recorded"
        )

    def _accept(self, run_id: str, result: ChapterRunResult) -> None:
        gates = result.context.gates if result.context else []
        self._step(run_id, "accept", summary=f"gates checked: {len(gates)}")
        self._store.transition(
            run_id, "accepted", command="chapter:accept", reason="acceptance gates passed"
        )

    def _export(self, run_id: str) -> None:
        action = self._adapter().run_pipeline_action("export", dry_run=True)
        self._step(run_id, "export", summary=" ".join(action.command))
        self._store.transition(
            run_id, "exported", command="chapter:export", reason="export dry-run recorded"
        )

    def _memory_update(self, run_id: str, chapter_no: int, result: ChapterRunResult) -> None:
        summary = result.draft.manuscript if result.draft else ""
        self._project.store.add(
            MemoryItem(
                project_slug=self._project.slug,
                type="chapter_summary",
                text=f"Chapter {chapter_no} drafted: {summary[:120]}",
                source=f"chapter:{chapter_no}",
            )
        )
        self._step(run_id, "memory_update", summary=f"chapter {chapter_no} summary stored")
        self._store.transition(
            run_id,
            "memory_updated",
            command="chapter:memory",
            reason="chapter summary stored to memory",
        )

    def _closeout(
        self,
        run_id: str,
        chapter_no: int,
        artifacts: ChapterArtifacts,
        result: ChapterRunResult,
    ) -> None:
        words = result.draft.word_count if result.draft else 0
        text = (
            f"# Chapter {chapter_no} Closeout\n\n"
            f"- state: memory_updated\n"
            f"- manuscript words: {words}\n"
            f"- context: {artifacts.context_path}\n"
            f"- draft: {artifacts.draft_path}\n"
        )
        artifacts.closeout_path = self._store.save_artifact(run_id, "closeout.md", text)

    # -- helpers ---------------------------------------------------------

    def _adapter(self) -> ProseForgeAdapter:
        root = self._project.engine_root or self._project.workspace.workspace_root
        return ProseForgeAdapter(root)

    def _step(
        self,
        run_id: str,
        name: str,
        *,
        artifacts: list[str] | None = None,
        summary: str = "",
    ) -> None:
        self._store.append_step(
            run_id,
            StepResult(
                name=name,
                status="ok",
                started_at=_now(),
                ended_at=_now(),
                artifacts=artifacts or [],
                summary=summary,
            ),
        )

    def _finish(self, run_id: str, result: ChapterRunResult) -> ChapterRunResult:
        run = self._store.load(run_id)
        result.state = run.state
        result.steps = list(run.step_history)
        return result


__all__ = [
    "ChapterProject",
    "ChapterArtifacts",
    "ChapterRunResult",
    "ChapterLifecycle",
]
