# Task 14: Rewrite And Accept Workflow

## Goal

Review drafts, plan targeted rewrites, apply revisions, and accept chapters with audit gates.

## Architecture Notes

Acceptance is editorial state. Failed gates require correction or an explicit audit reason.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chapter/review.py`
- Create `src/proseforge_agent/chapter/rewrite.py`
- Create `src/proseforge_agent/chapter/accept.py`
- Create `tests/test_chapter_review.py`
- Create `tests/test_rewrite_accept.py`

## Interfaces / Contracts

`ReviewReport` has findings, severity, gate results, citations, and recommendation. `RewritePlan` has issue ids, affected scenes, changes, risks, and acceptance criteria. `AcceptanceRecord` locks accepted text and reason.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_rewrite_accept.py::test_failed_gate_requires_audit_reason_for_force_accept`**

```python
def test_failed_gate_requires_audit_reason_for_force_accept(chapter_run):
    chapter_run.review.gates["continuity"] = "fail"
    with pytest.raises(AcceptanceError, match="audit reason"):
        ChapterAcceptor().accept(chapter_run, force=True, reason="")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_rewrite_accept.py::test_failed_gate_requires_audit_reason_for_force_accept -q
```

Expected: FAIL because review, rewrite, and accept modules are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement review prompt contract, gate evaluation, rewrite plan generator, revision validator, acceptance locking, force-accept audit, and review/rewrite reports.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_rewrite_accept.py::test_failed_gate_requires_audit_reason_for_force_accept -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_chapter_review.py tests/test_rewrite_accept.py -q
pf-agent chapter review --project demo --chapter 1 --provider fake --write
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/chapter/review.py tests
git commit -m "feat: add rewrite and accept workflow"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_chapter_review.py tests/test_rewrite_accept.py -q
pf-agent chapter review --project demo --chapter 1 --provider fake --write
```

## Acceptance

- Failed gates block normal acceptance.
- Force acceptance records a human-readable reason.
- Rewrites preserve source draft and change summary.
- Accepted chapter creates memory update candidates.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
