# Task 163: Execution Environment Abstraction

## Goal

Add an abstraction for local and remote execution environments used by terminal and tool execution.

## Architecture Notes

Execution environments are sandbox backends, not tools themselves. Tool policy decides whether a command may run; the selected environment decides where and how it runs.

## Files

- Create `src/proseforge_agent/environments/`.
- Add tests in `tests/environments/test_execution_environment_abstraction.py`.
- Add fixtures under `tests/environments/fixtures/`.

## Interfaces / Contracts

- `ExecutionEnvironment.run(command, cwd=None, env=None, timeout=None) -> ExecutionResult`.
- `ExecutionResult` includes stdout, stderr, exit code, duration, truncated flags, and artifact refs.
- Environments declare capabilities such as filesystem sync, long-running process, network, and gpu.

## TDD Steps

- [ ] Write failing test `tests/environments/test_execution_environment_abstraction.py::test_fake_environment_returns_execution_result`.
- [ ] Run `python -m pytest tests/environments/test_execution_environment_abstraction.py::test_fake_environment_returns_execution_result -q` and confirm failure.
- [ ] Implement protocol, fake environment, result model, and capability declarations.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for timeout, output truncation, env redaction, and unsupported capabilities.
- [ ] Run `python -m pytest tests/environments -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add execution environment abstraction`.

## Verification

```powershell
python -m pytest tests/environments/test_execution_environment_abstraction.py -q
pf-agent environments list --provider fake
python -m pytest -q
```

## Acceptance

- Tools can target an injected execution environment.
- Fake environment covers tests without shell side effects.
- Results are bounded and safe to persist.
- Permission policy remains outside the environment implementation.

## Commit Boundary

Commit only Task 163 environment abstraction files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

