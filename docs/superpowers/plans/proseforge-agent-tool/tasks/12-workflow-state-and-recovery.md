# Task 12: Workflow State And Recovery

## Goal

Persist workflow state so chapter work can pause, fail, resume, and audit every transition.

## Architecture Notes

Every long-running operation must leave recoverable state before and after external calls.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/workflow/state.py`
- Create `src/proseforge_agent/workflow/recovery.py`
- Create `tests/test_workflow_state.py`
- Create `tests/test_workflow_recovery.py`

## Interfaces / Contracts

`WorkflowRun` records id, project, chapter, state, step history, artifacts, provider attempts, retry count, timestamps, and audit entries. Valid states: created, context_ready, drafted, reviewed, needs_revision, revised, accepted, exported, memory_updated, failed, paused.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_workflow_state.py::test_invalid_workflow_transition_is_rejected`**

```python
def test_invalid_workflow_transition_is_rejected(tmp_path):
    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create(project_slug="demo", chapter_no=1)
    with pytest.raises(WorkflowStateError, match="created -> accepted"):
        store.transition(run.id, "accepted")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_workflow_state.py::test_invalid_workflow_transition_is_rejected -q
```

Expected: FAIL because workflow state store is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement state store, transition table, atomic artifact writes, provider attempt recording, pause/resume commands, and failure recovery reports.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_workflow_state.py::test_invalid_workflow_transition_is_rejected -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_workflow_state.py tests/test_workflow_recovery.py -q
pf-agent workflow status --project demo
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/workflow/state.py tests
git commit -m "feat: add workflow state and recovery"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_workflow_state.py tests/test_workflow_recovery.py -q
pf-agent workflow status --project demo
```

## Acceptance

- Invalid transitions fail before writing state.
- Interrupted runs resume from the last complete step.
- Audit records include command, actor, timestamp, and reason.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
