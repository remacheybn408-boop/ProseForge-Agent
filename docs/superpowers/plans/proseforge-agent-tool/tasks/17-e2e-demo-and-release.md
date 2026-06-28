# Task 17: End-To-End Demo And Release Hardening

## Goal

Prove the full product flow works with fake provider and portable paths.

## Architecture Notes

This is the release gate for the first usable Agent spine.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/demo.py`
- Create `src/proseforge_agent/release.py`
- Create `tests/test_e2e_demo.py`
- Create `tests/test_release_checks.py`
- Create `tests/fixtures/demo_project/`

## Interfaces / Contracts

`pf-agent demo run --provider fake` initializes a demo, certifies fake provider, creates intake, phase plan, daily workbook, chapter draft, review report, memory candidates, export dry-run report, closeout, and final report pack.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_e2e_demo.py::test_fake_provider_demo_writes_required_artifacts`**

```python
def test_fake_provider_demo_writes_required_artifacts(tmp_path):
    result = DemoRunner(tmp_path).run(provider="fake")
    assert result.status == "ok"
    assert result.daily_workbook.exists()
    assert result.chapter_draft.exists()
    assert result.report_pack.exists()
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_e2e_demo.py::test_fake_provider_demo_writes_required_artifacts -q
```

Expected: FAIL because demo runner is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement demo runner, release checks, fake project fixtures, portable environment checks, docs example verification, and final report pack generation.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_e2e_demo.py::test_fake_provider_demo_writes_required_artifacts -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_e2e_demo.py tests/test_release_checks.py -q
pf-agent demo run --provider fake --write-report
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/demo.py tests
git commit -m "feat: add e2e demo and release checks"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_e2e_demo.py tests/test_release_checks.py -q
pf-agent demo run --provider fake --write-report
```

## Acceptance

- Demo uses no real API keys.
- No demo command contains a machine-specific path.
- Release check fails if provider certification, memory audit, docs examples, or fake demo are missing.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
