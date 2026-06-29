# Task 168: Process Registry And Terminal Lifecycle

## Goal

Track long-running terminal processes and provide safe read, interrupt, close, and cleanup operations.

## Architecture Notes

Process lifecycle belongs to the execution layer and event bus. Tools and gateways interact through typed process ids, not raw OS handles.

## Files

- Create `src/proseforge_agent/environments/process_registry.py`.
- Extend terminal tools under `src/proseforge_agent/agent/` as needed.
- Add tests in `tests/environments/test_process_registry_terminal_lifecycle.py`.

## Interfaces / Contracts

- `ProcessRegistry.start(...)`, `read(process_id)`, `interrupt(process_id)`, `close(process_id)`, and `cleanup_stale()`.
- `pf-agent processes list`
- Registry entries store command summary, environment id, status, timestamps, and redacted output refs.

## TDD Steps

- [ ] Write failing test `tests/environments/test_process_registry_terminal_lifecycle.py::test_process_registry_tracks_start_read_close`.
- [ ] Run `python -m pytest tests/environments/test_process_registry_terminal_lifecycle.py::test_process_registry_tracks_start_read_close -q` and confirm failure.
- [ ] Implement process registry, fake process backend, lifecycle transitions, and stale cleanup.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for interrupt, missing process id, output truncation, crash recovery, and permission denial.
- [ ] Run `python -m pytest tests/environments/test_process_registry_terminal_lifecycle.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add process registry and terminal lifecycle`.

## Verification

```powershell
python -m pytest tests/environments/test_process_registry_terminal_lifecycle.py -q
pf-agent processes list
python -m pytest -q
```

## Acceptance

- Long-running processes can be inspected and stopped safely.
- Process records survive restart when configured.
- Output is bounded and redacted.
- Permission policy gates interrupts and closes.

## Commit Boundary

Commit only Task 168 process registry, terminal lifecycle, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

