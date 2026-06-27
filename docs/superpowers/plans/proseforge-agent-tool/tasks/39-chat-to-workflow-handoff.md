# Task 39: Chat-To-Workflow Handoff

## Goal

Convert chat decisions into explicit workflow handoff packages.

## Agent Product Requirement

A user should be able to say what they want conversationally and then approve a concrete workflow action.

## Architecture Notes

`ChatWorkflowHandoff` produces a handoff package that the Agent Kernel (Task 31) can hand to the workflow engine (Task 12+). Creating a handoff never starts a workflow on its own: a write-level workflow always requires an explicit permission grant and human confirmation before it runs. The handoff carries the evidence pack id so the workflow starts from the same context the chat discussed. It calls no provider and mutates no project state.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Chat-To-Workflow Handoff section)
- ../architecture/06-workflow-engine.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chat/handoff.py`
- Create `tests/test_chat_workflow_handoff.py`
- Create `tests/fixtures/chat-to-workflow-handoff/handoff_example.json`

## Interfaces / Contracts

- `ChatWorkflowHandoff.create(session_id, workflow, project_slug, chapter_no=None, evidence_pack_id=None) -> HandoffPackage`.
- `HandoffPackage` fields match architecture 08: `handoff_id`, `from_session_id`, `target_workflow`, `project_slug`, `chapter_no`, `intent_summary`, `evidence_pack_id`, `permission_required`, `human_confirmation`.
- `permission_required` is derived from the target workflow (e.g. `chapter_lifecycle` → `draft_write`); `human_confirmation` defaults to `True` for any write-level workflow.
- A handoff with `human_confirmation=True` and no recorded confirmation must not be marked runnable.

## Data Flow

1. Read the chat decision (workflow, project, optional chapter).
2. Resolve the permission level required by the target workflow.
3. Attach the evidence pack id from the chat context.
4. Set `human_confirmation` based on the permission level.
5. Persist the handoff package and return it for kernel approval.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_workflow_handoff.py::test_handoff_requires_permission_before_chapter_run`**

```python
def test_handoff_requires_permission_before_chapter_run():
    pkg = ChatWorkflowHandoff.create(
        session_id="s1", workflow="chapter_lifecycle", project_slug="demo", chapter_no=3
    )
    assert pkg.permission_required == "draft_write"
    assert pkg.human_confirmation is True
    assert pkg.is_runnable() is False  # not yet confirmed
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_workflow_handoff.py::test_handoff_requires_permission_before_chapter_run -q
```

Expected: FAIL because `ChatWorkflowHandoff` and `HandoffPackage` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ChatWorkflowHandoff`, `HandoffPackage`, permission derivation, confirmation gating, and persistence.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_workflow_handoff.py::test_handoff_requires_permission_before_chapter_run -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_confirmed_handoff_becomes_runnable
test_read_only_workflow_needs_no_human_confirmation
test_handoff_carries_evidence_pack_id_from_chat
test_unknown_workflow_raises_configuration_error
test_handoff_record_round_trips_utf8_intent_summary
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_workflow_handoff.py -q
pf-agent chat --message "继续第 3 章的改稿" --project demo --provider fake --propose-handoff
```

Expected: tests pass and chat proposes a handoff that is not runnable until confirmed.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/handoff.py tests/test_chat_workflow_handoff.py tests/fixtures/chat-to-workflow-handoff
git commit -m "feat: add chat workflow handoff"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- `intent_summary` and all text fields are UTF-8 and round-trip Chinese text.
- Handoff records use relative paths and opaque ids, no drive letters.
- Tests do not require provider keys or network.

## Failure Modes To Prove

- An unconfirmed write-level handoff reports `is_runnable() == False`.
- Unknown workflow name raises `ConfigurationError`.
- Missing project slug for a project workflow produces a recovery command.
- A handoff never starts a workflow as a side effect of creation.

## Verification

```powershell
python -m pytest tests/test_chat_workflow_handoff.py -q
pf-agent chat --message "继续第 3 章的改稿" --project demo --provider fake --propose-handoff
```

## Acceptance

- Chat produces explicit handoff packages, never silent workflow starts.
- Write-level handoffs require permission and human confirmation.
- The handoff carries the chat evidence pack id.
- Handoff shape matches architecture 08.

## Commit Boundary

Commit only chat handoff files and tests after verification passes. Do not start or modify workflow engine internals here.
