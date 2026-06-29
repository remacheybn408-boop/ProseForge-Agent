# Task 182: Middleware Hooks And Trajectory Datasets

## Goal

Add behavior-changing middleware hooks and research-ready trajectory dataset export.

## Architecture Notes

Middleware is powerful and must be explicitly enabled, ordered, permission-gated, and observable. Trajectory export must redact secrets and private text by policy before leaving the workspace.

## Files

- Create `src/proseforge_agent/agent/middleware.py`.
- Create `src/proseforge_agent/eval/trajectories.py`.
- Add tests in `tests/test_middleware_hooks_trajectory_datasets.py`.

## Interfaces / Contracts

- Middleware kinds: `llm_request`, `llm_execution`, `tool_request`, and `tool_execution`.
- Middleware receives `next_call` for execution wrappers and records middleware trace entries.
- `pf-agent trajectories export --redact --format jsonl`.

## TDD Steps

- [ ] Write failing test `tests/test_middleware_hooks_trajectory_datasets.py::test_tool_request_middleware_rewrites_args_before_policy`.
- [ ] Run `python -m pytest tests/test_middleware_hooks_trajectory_datasets.py::test_tool_request_middleware_rewrites_args_before_policy -q` and confirm failure.
- [ ] Implement middleware registry, ordered execution, trace records, redaction, and trajectory exporter.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for fail-open middleware errors, disabled middleware, policy re-check, trajectory compression, and export redaction.
- [ ] Run `python -m pytest tests/test_middleware_hooks_trajectory_datasets.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add middleware hooks and trajectory datasets`.

## Verification

```powershell
python -m pytest tests/test_middleware_hooks_trajectory_datasets.py -q
pf-agent trajectories export --redact --format jsonl
python -m pytest -q
```

## Acceptance

- Middleware is opt-in and ordered deterministically.
- Rewritten requests and tool args are rechecked by downstream policy.
- Trajectory exports are redacted and schema-versioned.
- Research exports do not require network access.

## Commit Boundary

Commit only Task 182 middleware, trajectory, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

