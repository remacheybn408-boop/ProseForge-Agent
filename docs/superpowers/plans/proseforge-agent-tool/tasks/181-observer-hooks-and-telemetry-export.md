# Task 181: Observer Hooks And Telemetry Export

## Goal

Add observer hooks and telemetry export for sessions, provider calls, tool calls, approvals, subagents, and jobs.

## Architecture Notes

Observer hooks are read-only. They report what happened with correlation ids and sanitized payloads. They must not mutate requests, tool arguments, or runtime behavior.

## Files

- Create `src/proseforge_agent/agent/observability.py`.
- Extend `src/proseforge_agent/agent/events.py`.
- Add tests in `tests/test_observer_hooks_telemetry_export.py`.

## Interfaces / Contracts

- Hook families: session lifecycle, turn, provider request, tool call, approval, subagent, job.
- Payloads include schema version, session id, turn id, task id, timestamps, status, and sanitized data.
- `pf-agent telemetry export --format jsonl --redact`.

## TDD Steps

- [ ] Write failing test `tests/test_observer_hooks_telemetry_export.py::test_observer_hook_receives_sanitized_tool_call_payload`.
- [ ] Run `python -m pytest tests/test_observer_hooks_telemetry_export.py::test_observer_hook_receives_sanitized_tool_call_payload -q` and confirm failure.
- [ ] Implement observer registry, payload schemas, redaction, event bridge, and JSONL export.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for fail-open observer errors, correlation ids, approval events, subagent events, and export filters.
- [ ] Run `python -m pytest tests/test_observer_hooks_telemetry_export.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add observer hooks and telemetry export`.

## Verification

```powershell
python -m pytest tests/test_observer_hooks_telemetry_export.py -q
pf-agent telemetry export --format jsonl --redact
python -m pytest -q
```

## Acceptance

- Observers cannot change runtime behavior.
- Payloads are versioned, correlated, and redacted.
- Observer failures are fail-open and logged.
- Exports are deterministic and support-bundle compatible.

## Commit Boundary

Commit only Task 181 observability/event files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

