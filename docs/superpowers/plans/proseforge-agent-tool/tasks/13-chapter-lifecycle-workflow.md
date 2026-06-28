# Task 13: Chapter Lifecycle Workflow

## Goal

Run prepare, draft, review, accept, export dry-run, memory update, and closeout as a chapter lifecycle.

## Architecture Notes

This card connects previous subsystems but still uses fake provider and dry-run export by default.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chapter/context.py`
- Create `src/proseforge_agent/chapter/draft.py`
- Create `src/proseforge_agent/chapter/lifecycle.py`
- Create `tests/test_chapter_lifecycle.py`
- Create `tests/fixtures/chapter/roadmap.json`

## Interfaces / Contracts

`ChapterContextPackage` includes roadmap, evidence pack, previous summary, target length, scene beats, constraints, and gates. `ChapterRunResult` records artifacts for each lifecycle step.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chapter_lifecycle.py::test_chapter_run_produces_draft_and_state_artifacts`**

```python
def test_chapter_run_produces_draft_and_state_artifacts(fake_project):
    result = ChapterLifecycle(fake_project).run(chapter_no=1, provider_name="fake", until="draft")
    assert result.state == "drafted"
    assert result.artifacts.draft_path.exists()
    assert result.artifacts.context_path.exists()
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_chapter_lifecycle.py::test_chapter_run_produces_draft_and_state_artifacts -q
```

Expected: FAIL because chapter lifecycle is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement context package builder, draft prompt builder, draft validator, lifecycle orchestration, artifact naming, and state transitions.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_chapter_lifecycle.py::test_chapter_run_produces_draft_and_state_artifacts -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_chapter_lifecycle.py -q
pf-agent chapter run --project demo --chapter 1 --until draft --provider fake
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/chapter/context.py tests
git commit -m "feat: add chapter lifecycle workflow"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_chapter_lifecycle.py -q
pf-agent chapter run --project demo --chapter 1 --until draft --provider fake
```

## Acceptance

- No draft runs without an evidence pack.
- Draft artifacts include text and structured metadata.
- Workflow state records context and draft paths.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
