import pytest

from proseforge_agent.workflow.recovery import WorkflowRecovery
from proseforge_agent.workflow.state import (
    StepResult,
    WorkflowStateError,
    WorkflowStateStore,
)


def _drafted_run(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    store.transition(run.id, "context_ready")
    store.transition(run.id, "drafted")
    return store, run.id


def test_paused_run_resumes_to_prior_state(tmp_path):
    store, run_id = _drafted_run(tmp_path)
    store.pause(run_id)
    assert store.load(run_id).state == "paused"
    resumed = WorkflowRecovery(store).resume(run_id)
    assert resumed.state == "drafted"


def test_recovery_report_identifies_last_complete_step(tmp_path):
    store, run_id = _drafted_run(tmp_path)
    store.append_step(run_id, StepResult(name="prepare", status="ok", started_at="t0"))
    store.append_step(run_id, StepResult(name="draft", status="ok", started_at="t1"))
    report = WorkflowRecovery(store).inspect(run_id)
    assert report.last_complete_step == "draft"


def test_failed_run_can_resume_for_retry(tmp_path):
    store, run_id = _drafted_run(tmp_path)
    store.fail(run_id, reason="provider error")
    assert store.load(run_id).state == "failed"
    resumed = WorkflowRecovery(store).resume(run_id)
    assert resumed.state == "drafted"
    assert resumed.retry_count == 1


def test_terminal_run_is_not_resumable(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    for state in ("context_ready", "drafted", "reviewed", "accepted", "exported", "memory_updated"):
        store.transition(run.id, state)
    report = WorkflowRecovery(store).inspect(run.id)
    assert report.resumable is False
    with pytest.raises(WorkflowStateError):
        WorkflowRecovery(store).resume(run.id)


def test_recovery_report_has_next_action(tmp_path):
    store, run_id = _drafted_run(tmp_path)
    store.pause(run_id)
    report = WorkflowRecovery(store).inspect(run_id)
    assert report.resumable is True
    assert report.next_action
