import pytest

from proseforge_agent.workflow.state import (
    StepResult,
    WorkflowStateError,
    WorkflowStateStore,
)


def test_invalid_workflow_transition_is_rejected(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    with pytest.raises(WorkflowStateError, match="created -> accepted"):
        store.transition(run.id, "accepted")


def test_create_starts_in_created_state(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    assert run.state == "created"
    assert run.project_slug == "demo"
    assert run.chapter_no == 1


def test_valid_transition_updates_state(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    updated = store.transition(run.id, "context_ready")
    assert updated.state == "context_ready"


def test_full_happy_path_lifecycle(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    for state in (
        "context_ready",
        "drafted",
        "reviewed",
        "accepted",
        "exported",
        "memory_updated",
    ):
        run = store.transition(run.id, state)
    assert run.state == "memory_updated"


def test_invalid_transition_does_not_write_state(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    with pytest.raises(WorkflowStateError):
        store.transition(run.id, "accepted")
    assert store.load(run.id).state == "created"


def test_transition_records_audit_entry(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    store.transition(
        run.id, "context_ready", actor="writer", reason="evidence ready", command="pf-agent chapter"
    )
    entry = store.load(run.id).audit[-1]
    assert entry.command == "pf-agent chapter"
    assert entry.actor == "writer"
    assert entry.reason == "evidence ready"
    assert entry.timestamp


def test_append_step_records_history(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    store.append_step(
        run.id, StepResult(name="retrieve_evidence", status="ok", started_at="t0")
    )
    history = store.load(run.id).step_history
    assert history[-1].name == "retrieve_evidence"


def test_record_provider_attempt(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    store.record_provider_attempt(run.id, {"provider": "fake", "status": "error"})
    reloaded = store.load(run.id)
    assert reloaded.provider_attempts[-1]["provider"] == "fake"
    assert reloaded.retry_count == 1


def test_save_artifact_is_atomic_and_recorded(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    path = store.save_artifact(run.id, "draft.md", "hello")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "hello"
    assert str(path) in store.load(run.id).artifacts


def test_run_persists_across_reload(tmp_path):
    runs_dir = tmp_path / "runs"
    run = WorkflowStateStore(runs_dir).create(project_slug="demo", chapter_no=2)
    WorkflowStateStore(runs_dir).transition(run.id, "context_ready")
    assert WorkflowStateStore(runs_dir).load(run.id).state == "context_ready"
