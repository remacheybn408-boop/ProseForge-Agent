"""Inspect and resume interrupted workflow runs.

A paused or failed run can be resumed from the state it held before the
interruption, continuing from the last completed step. Terminal and in-progress
runs are not resumable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .state import WorkflowRun, WorkflowStateError, WorkflowStateStore

_RECOVERABLE = {"failed", "paused"}


@dataclass(frozen=True)
class RecoveryReport:
    """A diagnosis of whether and how a run can be recovered."""

    run_id: str
    current_state: str
    resumable: bool
    last_complete_step: str | None
    next_action: str
    reason: str


class WorkflowRecovery:
    """Diagnose and resume workflow runs."""

    def __init__(self, store: WorkflowStateStore) -> None:
        self._store = store

    def _last_complete_step(self, run: WorkflowRun) -> str | None:
        for step in reversed(run.step_history):
            if step.status == "ok":
                return step.name
        return None

    def inspect(self, run_id: str) -> RecoveryReport:
        run = self._store.load(run_id)
        resumable = run.state in _RECOVERABLE
        last_complete = self._last_complete_step(run)
        if resumable:
            next_action = f"Resume from {run.resume_state!r} after the last complete step"
            reason = f"run is {run.state} with a recorded resume state"
        else:
            next_action = "No recovery needed"
            reason = f"run is {run.state}"
        return RecoveryReport(
            run_id=run_id,
            current_state=run.state,
            resumable=resumable,
            last_complete_step=last_complete,
            next_action=next_action,
            reason=reason,
        )

    def resume(self, run_id: str) -> WorkflowRun:
        run = self._store.load(run_id)
        if run.state not in _RECOVERABLE:
            raise WorkflowStateError(f"run {run_id} in state {run.state!r} is not resumable")
        retry = run.state == "failed"
        return self._store.resume_to(run_id, retry=retry)


__all__ = ["RecoveryReport", "WorkflowRecovery"]
