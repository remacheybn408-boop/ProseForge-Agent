# Task 03: ProseForge Engine Adapter

## Goal

Detect and call the existing ProseForge engine through a safe adapter.

## Architecture Notes

The Agent orchestrates ProseForge; it does not copy the engine. All engine paths come from `AgentConfig.proseforge_root`.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/proseforge/__init__.py`
- Create `src/proseforge_agent/proseforge/adapter.py`
- Create `src/proseforge_agent/proseforge/results.py`
- Create `tests/fixtures/proseforge_engine/`
- Create `tests/test_proseforge_adapter.py`

## Interfaces / Contracts

`ProseForgeAdapter.discover()` returns capability flags; `run_project_action(action, args, dry_run=True)` returns an `EngineActionResult` with command, status, stdout, stderr, artifacts, and duration.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_proseforge_adapter.py::test_discover_reports_missing_and_present_scripts`**

```python
def test_discover_reports_missing_and_present_scripts(tmp_path):
    root = tmp_path / "engine"
    (root / "plugin/proseforge-codex/scripts").mkdir(parents=True)
    (root / "plugin/proseforge-codex/scripts/nf_project.py").write_text("print('ok')", encoding="utf-8")
    result = ProseForgeAdapter(root).discover()
    assert result.has_project_script is True
    assert result.has_pipeline_script is False
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_proseforge_adapter.py::test_discover_reports_missing_and_present_scripts -q
```

Expected: FAIL because `ProseForgeAdapter` is not defined.

- [ ] **Step 3: Implement the minimum production behavior**

Implement discovery, script-path construction from the configured root, dry-run command rendering, timeout-safe subprocess execution, and result serialization.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_proseforge_adapter.py::test_discover_reports_missing_and_present_scripts -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_proseforge_adapter.py -q
pf-agent proseforge inspect --root $env:PROSEFORGE_ROOT --dry-run
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/proseforge/__init__.py tests
git commit -m "feat: add proseforge engine adapter"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_proseforge_adapter.py -q
pf-agent proseforge inspect --root $env:PROSEFORGE_ROOT --dry-run
```

## Acceptance

- Adapter never assumes a fixed drive or folder.
- Dry-run prints the exact command without writing project artifacts.
- Missing engine scripts are warnings for inspect and errors for mutating actions.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
