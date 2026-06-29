# Task 156: Platform Adapter Contract

## Goal

Define a stable contract for messaging platform adapters.

## Architecture Notes

Adapters own platform-specific authentication, inbound parsing, outbound formatting, and rate-limit semantics. The gateway core owns agent session routing and shared policy.

## Files

- Add `src/proseforge_agent/gateway/platforms/base.py`.
- Add tests in `tests/gateway/test_platform_adapter_contract.py`.
- Add fake adapter fixtures under `tests/gateway/fixtures/platforms/`.

## Interfaces / Contracts

- `PlatformAdapter.poll_or_listen()`, `send(message)`, `edit(message)`, `ack(event)`, and `health()`.
- `SendResult` reports delivered, retryable, message ids, continuation ids, and raw sanitized metadata.
- Adapters declare capabilities such as threads, edits, reactions, attachments, and max message size.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_platform_adapter_contract.py::test_fake_adapter_round_trips_message_event`.
- [ ] Run `python -m pytest tests/gateway/test_platform_adapter_contract.py::test_fake_adapter_round_trips_message_event -q` and confirm failure.
- [ ] Implement adapter protocol, fake adapter, capability declarations, and send result.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for capability checks, redacted raw metadata, retryable failures, and message-size limits.
- [ ] Run `python -m pytest tests/gateway/test_platform_adapter_contract.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add platform adapter contract`.

## Verification

```powershell
python -m pytest tests/gateway/test_platform_adapter_contract.py -q
pf-agent gateway platforms --provider fake
python -m pytest -q
```

## Acceptance

- All future platform adapters share one typed contract.
- Fake adapter supports deterministic tests.
- Capability declarations prevent unsupported platform actions.
- Sanitized metadata is safe for reports and support bundles.

## Commit Boundary

Commit only Task 156 adapter contract, fake adapter, tests, fixtures, and minimal CLI wiring. Do not bundle adjacent task cards.

