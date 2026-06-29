# Task 167: Remote File Sync And Checkpoints

## Goal

Add remote file synchronization and checkpoints for execution environments.

## Architecture Notes

File sync is explicit and scoped. The agent must never mirror arbitrary home directories or secrets. Checkpoints capture recoverable working state and artifact references.

## Files

- Create `src/proseforge_agent/environments/file_sync.py`.
- Create `src/proseforge_agent/environments/checkpoints.py`.
- Add tests in `tests/environments/test_remote_file_sync_checkpoints.py`.

## Interfaces / Contracts

- `FileSyncPlan` lists includes, excludes, root, destination, dry-run operations, and redactions.
- `EnvironmentCheckpoint` records backend id, project refs, artifact refs, created date, and restore plan.
- `pf-agent environments sync --dry-run`.

## TDD Steps

- [ ] Write failing test `tests/environments/test_remote_file_sync_checkpoints.py::test_sync_plan_excludes_secrets_and_outside_paths`.
- [ ] Run `python -m pytest tests/environments/test_remote_file_sync_checkpoints.py::test_sync_plan_excludes_secrets_and_outside_paths -q` and confirm failure.
- [ ] Implement sync plan generation, path containment, ignore rules, and checkpoint metadata.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for restore plan, deleted files, artifact refs, Windows paths, and large file limits.
- [ ] Run `python -m pytest tests/environments/test_remote_file_sync_checkpoints.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add remote file sync and checkpoints`.

## Verification

```powershell
python -m pytest tests/environments/test_remote_file_sync_checkpoints.py -q
pf-agent environments sync --dry-run
python -m pytest -q
```

## Acceptance

- Sync plans never include secrets or paths outside configured roots.
- Checkpoints can be listed and restored through deterministic plans.
- Plans are portable across Windows, macOS, and Linux.
- Dry-run mode is the default for destructive or remote operations.

## Commit Boundary

Commit only Task 167 sync/checkpoint files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

