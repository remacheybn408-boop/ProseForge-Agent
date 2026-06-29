# Task 164: Local And Docker Execution Backends

## Goal

Implement local and Docker execution backends behind the environment abstraction.

## Architecture Notes

The local backend is conservative and policy-gated. The Docker backend provides stronger isolation when Docker is available, but all tests must run without requiring Docker by using fake process runners.

## Files

- Create `src/proseforge_agent/environments/local.py`.
- Create `src/proseforge_agent/environments/docker.py`.
- Add tests in `tests/environments/test_local_docker_backends.py`.

## Interfaces / Contracts

- `pf-agent environments check local`
- `pf-agent environments check docker --dry-run`
- Docker backend supports image, workdir mount plan, env allowlist, timeout, and cleanup plan.

## TDD Steps

- [ ] Write failing test `tests/environments/test_local_docker_backends.py::test_local_backend_uses_safe_process_runner`.
- [ ] Run `python -m pytest tests/environments/test_local_docker_backends.py::test_local_backend_uses_safe_process_runner -q` and confirm failure.
- [ ] Implement local backend, Docker plan/check backend, and fake process runners.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for command policy handoff, Docker unavailable, mount path containment, timeout, and cleanup.
- [ ] Run `python -m pytest tests/environments/test_local_docker_backends.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add local and docker execution backends`.

## Verification

```powershell
python -m pytest tests/environments/test_local_docker_backends.py -q
pf-agent environments check local --dry-run
pf-agent environments check docker --dry-run
python -m pytest -q
```

## Acceptance

- Local execution uses the existing permission and sandbox policy.
- Docker checks are deterministic when Docker is unavailable.
- Mount and environment plans are redacted and path-contained.
- No test requires a real container runtime.

## Commit Boundary

Commit only Task 164 backend files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

