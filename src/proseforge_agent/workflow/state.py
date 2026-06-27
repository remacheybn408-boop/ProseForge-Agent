"""Durable workflow state with an auditable transition table.

Each chapter run is a JSON file under a runs directory. Every transition is
validated against the lifecycle table before anything is written, so an invalid
transition can never corrupt persisted state, and each transition appends an
audit entry. Artifacts are written atomically (temp file + os.replace) so an
interrupted write never leaves a half-written file.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..errors import ProseForgeAgentError


class WorkflowStateError(ProseForgeAgentError):
    """Raised on an invalid workflow transition or an unrecoverable resume."""


VALID_STATES: tuple[str, ...] = (
    "created",
    "context_ready",
    "drafted",
    "reviewed",
    "needs_revision",
    "revised",
    "accepted",
    "exported",
    "memory_updated",
    "failed",
    "paused",
)

# Recovery (pause/fail -> resume) is handled by WorkflowRecovery, not by the
# plain transition table.
_RECOVERABLE = {"failed", "paused"}

ALLOWED: dict[str, set[str]] = {
    "created": {"context_ready", "failed", "paused"},
    "context_ready": {"drafted", "failed", "paused"},
    "drafted": {"reviewed", "failed", "paused"},
    "reviewed": {"accepted", "needs_revision", "failed", "paused"},
    "needs_revision": {"revised", "failed", "paused"},
    "revised": {"reviewed", "failed", "paused"},
    "accepted": {"exported", "failed", "paused"},
    "exported": {"memory_updated", "failed", "paused"},
    "memory_updated": set(),
    "failed": set(),
    "paused": set(),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StepResult:
    """The outcome of one workflow step."""

    name: str
    status: str
    started_at: str
    ended_at: str = ""
    artifacts: list[str] = field(default_factory=list)
    summary: str = ""
    error: str = ""


@dataclass
class AuditEntry:
    """A record of one state transition."""

    command: str
    actor: str
    timestamp: str
    reason: str
    from_state: str
    to_state: str


@dataclass
class WorkflowRun:
    """Persisted state of one chapter workflow run."""

    id: str
    project_slug: str
    chapter_no: int
    state: str
    created_at: str
    updated_at: str
    step_history: list[StepResult] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    provider_attempts: list[dict] = field(default_factory=list)
    retry_count: int = 0
    audit: list[AuditEntry] = field(default_factory=list)
    resume_state: str | None = None


class WorkflowStateStore:
    """Create, transition, and persist workflow runs as JSON files."""

    def __init__(self, runs_dir: str | Path) -> None:
        self._dir = Path(runs_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # -- paths / io ------------------------------------------------------

    def _run_path(self, run_id: str) -> Path:
        return self._dir / f"{run_id}.json"

    def _atomic_write(self, path: Path, text: str) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def _save(self, run: WorkflowRun) -> WorkflowRun:
        run.updated_at = _now()
        self._atomic_write(self._run_path(run.id), json.dumps(asdict(run), ensure_ascii=False, indent=2))
        return run

    # -- lifecycle -------------------------------------------------------

    def create(self, project_slug: str, chapter_no: int) -> WorkflowRun:
        now = _now()
        run = WorkflowRun(
            id=f"run-{uuid.uuid4().hex[:8]}",
            project_slug=project_slug,
            chapter_no=chapter_no,
            state="created",
            created_at=now,
            updated_at=now,
        )
        run.audit.append(
            AuditEntry(
                command="create",
                actor="system",
                timestamp=now,
                reason="run created",
                from_state="",
                to_state="created",
            )
        )
        return self._save(run)

    def load(self, run_id: str) -> WorkflowRun:
        path = self._run_path(run_id)
        if not path.exists():
            raise WorkflowStateError(f"unknown workflow run {run_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return WorkflowRun(
            id=data["id"],
            project_slug=data["project_slug"],
            chapter_no=data["chapter_no"],
            state=data["state"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            step_history=[StepResult(**s) for s in data.get("step_history", [])],
            artifacts=list(data.get("artifacts", [])),
            provider_attempts=list(data.get("provider_attempts", [])),
            retry_count=data.get("retry_count", 0),
            audit=[AuditEntry(**a) for a in data.get("audit", [])],
            resume_state=data.get("resume_state"),
        )

    def transition(
        self,
        run_id: str,
        new_state: str,
        *,
        actor: str = "system",
        reason: str = "",
        command: str = "",
    ) -> WorkflowRun:
        run = self.load(run_id)
        if new_state not in ALLOWED.get(run.state, set()):
            raise WorkflowStateError(
                f"invalid transition {run.state} -> {new_state}"
            )
        run.audit.append(
            AuditEntry(
                command=command or f"transition:{new_state}",
                actor=actor,
                timestamp=_now(),
                reason=reason,
                from_state=run.state,
                to_state=new_state,
            )
        )
        run.state = new_state
        return self._save(run)

    def pause(self, run_id: str, *, actor: str = "system", reason: str = "paused") -> WorkflowRun:
        run = self.load(run_id)
        run.resume_state = run.state
        self._save(run)  # persist resume_state before the paused transition
        return self.transition(run_id, "paused", actor=actor, reason=reason, command="pause")

    def fail(self, run_id: str, *, reason: str = "failed", actor: str = "system") -> WorkflowRun:
        run = self.load(run_id)
        run.resume_state = run.state
        self._save(run)  # persist resume_state before the failed transition
        return self.transition(run_id, "failed", actor=actor, reason=reason, command="fail")

    def resume_to(
        self, run_id: str, *, retry: bool = False, actor: str = "system"
    ) -> WorkflowRun:
        """Sanctioned recovery transition out of a paused/failed run.

        Bypasses the normal transition table (paused/failed have no forward
        edges) and restores the state recorded when the run was paused/failed.
        """
        run = self.load(run_id)
        if run.state not in _RECOVERABLE:
            raise WorkflowStateError(f"run {run_id} in state {run.state!r} is not resumable")
        target = run.resume_state
        if not target:
            raise WorkflowStateError(f"run {run_id} has no resume state recorded")
        run.audit.append(
            AuditEntry(
                command="resume",
                actor=actor,
                timestamp=_now(),
                reason="resume from " + run.state,
                from_state=run.state,
                to_state=target,
            )
        )
        run.state = target
        run.resume_state = None
        if retry:
            run.retry_count += 1
        return self._save(run)

    # -- step / provider / artifact -------------------------------------

    def append_step(self, run_id: str, step: StepResult) -> WorkflowRun:
        run = self.load(run_id)
        run.step_history.append(step)
        return self._save(run)

    def record_provider_attempt(self, run_id: str, attempt: dict) -> WorkflowRun:
        run = self.load(run_id)
        run.provider_attempts.append(attempt)
        run.retry_count = len(run.provider_attempts)
        return self._save(run)

    def save_artifact(self, run_id: str, name: str, content: str) -> Path:
        run = self.load(run_id)
        artifact_dir = self._dir / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        path = artifact_dir / name
        self._atomic_write(path, content)
        if str(path) not in run.artifacts:
            run.artifacts.append(str(path))
        self._save(run)
        return path

    def list(self, project_slug: str | None = None) -> list[WorkflowRun]:
        runs = []
        for path in sorted(self._dir.glob("run-*.json")):
            run = self.load(path.stem)
            if project_slug is None or run.project_slug == project_slug:
                runs.append(run)
        return runs


__all__ = [
    "WorkflowStateError",
    "VALID_STATES",
    "ALLOWED",
    "StepResult",
    "AuditEntry",
    "WorkflowRun",
    "WorkflowStateStore",
]
