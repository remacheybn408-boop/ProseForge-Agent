# Task 155: Messaging Gateway Core

## Goal

Add a platform-neutral messaging gateway core for non-desktop remote conversations.

## Architecture Notes

The gateway converts platform events into agent turns and delivery jobs. It must reuse the agent kernel, session store, permission policy, event bus, and provider registry without owning domain logic.

## Files

- Create `src/proseforge_agent/gateway/`.
- Add tests in `tests/gateway/test_messaging_gateway_core.py`.
- Add fixtures under `tests/gateway/fixtures/core/` when needed.

## Interfaces / Contracts

- `GatewayRunner.start()` and `GatewayRunner.handle_event(event)`.
- `MessageEvent` includes platform, chat id, user id, thread id, message id, text, attachments, and authorization metadata.
- `pf-agent gateway run --provider fake --check`.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_messaging_gateway_core.py::test_gateway_routes_message_to_agent_session`.
- [ ] Run `python -m pytest tests/gateway/test_messaging_gateway_core.py::test_gateway_routes_message_to_agent_session -q` and confirm failure.
- [ ] Implement message event types, runner orchestration, delivery queue, and check mode.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for unauthorized users, thread keys, crash-safe queue persistence, and graceful shutdown.
- [ ] Run `python -m pytest tests/gateway -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add messaging gateway core`.

## Verification

```powershell
python -m pytest tests/gateway/test_messaging_gateway_core.py -q
pf-agent gateway run --provider fake --check
python -m pytest -q
```

## Acceptance

- Gateway check mode works without real platform credentials.
- Platform events map to deterministic session keys.
- Delivery jobs are append-only and crash recoverable.
- No platform adapter stores raw secrets in config or logs.

## Commit Boundary

Commit only Task 155 gateway core files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

