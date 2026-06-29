# Task 165: SSH And Singularity Execution Backends

## Goal

Add SSH and Singularity execution backend plans for remote machines and research clusters.

## Architecture Notes

These backends must be optional, dry-run first, and credential-safe. Real network connections are never required by tests.

## Files

- Create `src/proseforge_agent/environments/ssh.py`.
- Create `src/proseforge_agent/environments/singularity.py`.
- Add tests in `tests/environments/test_ssh_singularity_backends.py`.

## Interfaces / Contracts

- `pf-agent environments check ssh --profile <name> --dry-run`
- `pf-agent environments check singularity --image <path> --dry-run`
- Backends return execution plans, connection health, and unsupported-capability diagnostics.

## TDD Steps

- [ ] Write failing test `tests/environments/test_ssh_singularity_backends.py::test_ssh_backend_redacts_connection_plan`.
- [ ] Run `python -m pytest tests/environments/test_ssh_singularity_backends.py::test_ssh_backend_redacts_connection_plan -q` and confirm failure.
- [ ] Implement dry-run connection planning, command wrapping, redaction, and capability checks.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for missing ssh binary, missing singularity binary, host key policy, path sync plan, and timeout.
- [ ] Run `python -m pytest tests/environments/test_ssh_singularity_backends.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add ssh and singularity execution backends`.

## Verification

```powershell
python -m pytest tests/environments/test_ssh_singularity_backends.py -q
pf-agent environments check ssh --profile demo --dry-run
python -m pytest -q
```

## Acceptance

- SSH and Singularity are optional and dry-run testable.
- Credentials and host details are redacted in reports.
- Backends declare unsupported capabilities clearly.
- No test opens a real network connection.

## Commit Boundary

Commit only Task 165 backend files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

