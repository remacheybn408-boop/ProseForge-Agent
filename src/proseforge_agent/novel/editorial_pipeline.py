"""Editorial pipeline: stage chapters through a real novel editing workflow."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .draft_versioning import DraftVersionStore


EDITORIAL_DIR = "editorial"
STATE_NAME = "state.json"

EDITORIAL_STAGES = (
    "outline",
    "rough_draft",
    "structure_edit",
    "style_edit",
    "continuity_check",
    "copy_edit",
    "final",
)

STAGE_DOD = {
    "outline": "章节目标、冲突与转折点已列出。",
    "rough_draft": "完整初稿成形，情节连贯。",
    "structure_edit": "场景顺序与节奏已校订。",
    "style_edit": "语气与文风已统一。",
    "continuity_check": "设定与时间线无冲突。",
    "copy_edit": "错别字与标点已校对。",
    "final": "终稿锁定，可交付。",
}


@dataclass(frozen=True)
class StageArtifact:
    """One produced editorial-stage artifact."""

    stage: str
    chapter: str
    path: Path
    dod: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["path"] = str(self.path)
        return data


@dataclass(frozen=True)
class PipelineState:
    """Editorial state for one chapter."""

    chapter: str
    current_stage: str
    completed: list[str] = field(default_factory=list)
    artifacts: list[StageArtifact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "current_stage": self.current_stage,
            "completed": list(self.completed),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }


@dataclass(frozen=True)
class PromoteResult:
    """Outcome of an approval-gated stage promotion."""

    chapter: str
    to: str
    status: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineStatus:
    """Editorial status across all chapters in a project."""

    chapters: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"chapters": list(self.chapters)}


class EditorialPipeline:
    """Drive chapters through outline -> ... -> final as a real editorial workflow."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.editorial_root = self.project_root / EDITORIAL_DIR

    def run(self, chapter: str) -> PipelineState:
        text = self._chapter_text(chapter)
        completed: list[str] = []
        artifacts: list[StageArtifact] = []
        for stage in EDITORIAL_STAGES:
            if stage == "final":
                break  # final is reached only through an approved promote
            artifacts.append(self._write_stage(chapter, stage, text))
            completed.append(stage)
        current = completed[-1] if completed else "outline"
        self._save_state(chapter, {"current_stage": current, "completed": completed})
        return PipelineState(chapter=chapter, current_stage=current, completed=completed, artifacts=artifacts)

    def promote(self, chapter: str, *, to: str, approve: bool = False) -> PromoteResult:
        if to not in EDITORIAL_STAGES:
            raise ValueError(f"unknown editorial stage {to!r}")
        high_risk = to == "final"
        if high_risk and not approve:
            return PromoteResult(chapter=chapter, to=to, status="pending_approval", approved=False)
        text = self._chapter_text(chapter)
        self._write_stage(chapter, to, text)
        state = self._load_state(chapter)
        if to not in state["completed"]:
            state["completed"].append(to)
        state["current_stage"] = to
        self._save_state(chapter, state)
        if to == "final":
            DraftVersionStore(self.root, slug=self.slug).commit(chapter, text, provider="editorial", prompt="final")
        return PromoteResult(chapter=chapter, to=to, status="promoted", approved=approve or not high_risk)

    def status(self) -> PipelineStatus:
        chapters: list[dict[str, Any]] = []
        if self.editorial_root.exists():
            for state_path in sorted(self.editorial_root.glob(f"*/{STATE_NAME}")):
                state = json.loads(state_path.read_text(encoding="utf-8"))
                chapters.append(
                    {
                        "chapter": state_path.parent.name,
                        "current_stage": state.get("current_stage", "outline"),
                        "completed": state.get("completed", []),
                    }
                )
        return PipelineStatus(chapters=chapters)

    # -- internals -------------------------------------------------------

    def _chapter_text(self, chapter: str) -> str:
        path = self.project_root / "chapters" / f"{chapter}.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _write_stage(self, chapter: str, stage: str, text: str) -> StageArtifact:
        path = self.editorial_root / chapter / f"{stage}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        dod = STAGE_DOD[stage]
        body = "\n".join(
            [
                f"# Editorial Stage: {stage} — {chapter}",
                "",
                f"DoD: {dod}",
                "",
                "## Working Copy",
                "",
                text,
                "",
            ]
        )
        path.write_text(body, encoding="utf-8")
        return StageArtifact(stage=stage, chapter=chapter, path=path, dod=dod, status="done")

    def _state_path(self, chapter: str) -> Path:
        return self.editorial_root / chapter / STATE_NAME

    def _load_state(self, chapter: str) -> dict[str, Any]:
        path = self._state_path(chapter)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"current_stage": "outline", "completed": []}

    def _save_state(self, chapter: str, state: dict[str, Any]) -> None:
        path = self._state_path(chapter)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "EDITORIAL_DIR",
    "EDITORIAL_STAGES",
    "STAGE_DOD",
    "EditorialPipeline",
    "PipelineState",
    "PipelineStatus",
    "PromoteResult",
    "StageArtifact",
]
