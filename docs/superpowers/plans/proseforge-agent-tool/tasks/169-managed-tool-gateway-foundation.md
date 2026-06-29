# Task 169: Managed Tool Gateway Foundation

## Goal

Add a managed tool gateway abstraction for externally hosted tools such as search, browser, media generation, and transcription.

## Architecture Notes

The managed gateway is a credential and routing boundary. It should not hide tool permissions or collapse all tools into one unsafe super-tool.

## Files

- Create `src/proseforge_agent/tools/managed/`.
- Add tests in `tests/tools/test_managed_tool_gateway_foundation.py`.
- Add fake gateway fixtures under `tests/tools/fixtures/managed-gateway/`.

## Interfaces / Contracts

- `ManagedToolGateway.invoke(tool_name, payload, policy_context) -> ManagedToolResult`.
- Tool declarations include permission level, credential scope, cost hints, and output limits.
- `pf-agent tools gateway check --provider fake`.

## TDD Steps

- [ ] Write failing test `tests/tools/test_managed_tool_gateway_foundation.py::test_gateway_invocation_enforces_tool_declaration`.
- [ ] Run `python -m pytest tests/tools/test_managed_tool_gateway_foundation.py::test_gateway_invocation_enforces_tool_declaration -q` and confirm failure.
- [ ] Implement gateway protocol, fake gateway, declarations, redaction, and result model.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for unknown tools, denied permissions, missing credentials, cost hints, and output limits.
- [ ] Run `python -m pytest tests/tools/test_managed_tool_gateway_foundation.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add managed tool gateway foundation`.

## Verification

```powershell
python -m pytest tests/tools/test_managed_tool_gateway_foundation.py -q
pf-agent tools gateway check --provider fake
python -m pytest -q
```

## Acceptance

- Managed tools are declared and permission-gated individually.
- Credentials are scoped per backend and redacted.
- Fake gateway supports deterministic offline tests.
- Results can be stored as bounded artifacts.

## Commit Boundary

Commit only Task 169 managed gateway files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

