# Task 160: Gateway Relay Auth And Pairing

## Goal

Add relay authentication and pairing so remote connectors can deliver messages to a gateway without exposing platform secrets to the agent runtime.

## Architecture Notes

The relay boundary separates platform credential ownership from agent execution. Gateway instances authenticate to a connector with short-lived or enrolled credentials and receive sanitized events.

## Files

- Create `src/proseforge_agent/gateway/relay/`.
- Add tests in `tests/gateway/test_gateway_relay_auth_pairing.py`.
- Add fixtures under `tests/gateway/fixtures/relay/`.

## Interfaces / Contracts

- `pf-agent gateway pair --platform telegram --dry-run`
- `pf-agent gateway relay check`
- Relay tokens are scoped to gateway instance id, profile, platform, and expiration.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_gateway_relay_auth_pairing.py::test_pairing_token_is_scoped_and_redacted`.
- [ ] Run `python -m pytest tests/gateway/test_gateway_relay_auth_pairing.py::test_pairing_token_is_scoped_and_redacted -q` and confirm failure.
- [ ] Implement pairing tokens, relay auth validation, redaction, and check command.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for expired tokens, wrong audience, revoked enrollment, and sanitized inbound events.
- [ ] Run `python -m pytest tests/gateway/test_gateway_relay_auth_pairing.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add gateway relay auth and pairing`.

## Verification

```powershell
python -m pytest tests/gateway/test_gateway_relay_auth_pairing.py -q
pf-agent gateway relay check --dry-run
python -m pytest -q
```

## Acceptance

- Pairing never writes raw platform secrets into the agent config.
- Relay events are authenticated and sanitized before session routing.
- Expired or wrong-audience tokens are rejected.
- Dry-run mode is deterministic and offline.

## Commit Boundary

Commit only Task 160 relay, auth, pairing, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

