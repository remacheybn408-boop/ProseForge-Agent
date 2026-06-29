# Task 166: Modal And Daytona Execution Backends

## Goal

Add Modal and Daytona-style serverless execution backend plans for hibernating remote agent environments.

## Architecture Notes

This card implements configuration, dry-run planning, lifecycle state, and fake-client tests. It must not require real Modal or Daytona accounts.

## Files

- Create `src/proseforge_agent/environments/modal.py`.
- Create `src/proseforge_agent/environments/daytona.py`.
- Add tests in `tests/environments/test_modal_daytona_backends.py`.

## Interfaces / Contracts

- `pf-agent environments check modal --dry-run`
- `pf-agent environments check daytona --dry-run`
- Lifecycle states include missing_config, ready, waking, running, hibernating, failed, and unavailable.

## TDD Steps

- [ ] Write failing test `tests/environments/test_modal_daytona_backends.py::test_serverless_backend_reports_hibernation_plan`.
- [ ] Run `python -m pytest tests/environments/test_modal_daytona_backends.py::test_serverless_backend_reports_hibernation_plan -q` and confirm failure.
- [ ] Implement fake-client lifecycle planning, config validation, redaction, and dry-run checks.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for missing credentials, wake timeout, artifact sync plan, provider unavailable, and hibernation state persistence.
- [ ] Run `python -m pytest tests/environments/test_modal_daytona_backends.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add modal and daytona execution backends`.

## Verification

```powershell
python -m pytest tests/environments/test_modal_daytona_backends.py -q
pf-agent environments check modal --dry-run
pf-agent environments check daytona --dry-run
python -m pytest -q
```

## Acceptance

- Serverless backend planning is deterministic in offline tests.
- Hibernation and wake states are explicit.
- Credentials are redacted and stored through the secret boundary.
- Unsupported platforms fail with actionable diagnostics.

## Commit Boundary

Commit only Task 166 backend files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

