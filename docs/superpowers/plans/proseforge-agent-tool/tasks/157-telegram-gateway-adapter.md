# Task 157: Telegram Gateway Adapter

## Goal

Add a Telegram gateway adapter with deterministic fake-HTTP tests and no real network requirement.

## Architecture Notes

Telegram support must sit behind the platform adapter contract from Task 156. Runtime secrets must come from the secret store or environment and must never appear in logs, support bundles, or reports.

## Files

- Create `src/proseforge_agent/gateway/platforms/telegram.py`.
- Add tests in `tests/gateway/test_telegram_gateway_adapter.py`.
- Add fixtures under `tests/gateway/fixtures/telegram/`.

## Interfaces / Contracts

- `pf-agent gateway telegram setup --dry-run`
- `pf-agent gateway telegram check`
- Adapter supports inbound messages, threaded topics when present, send, edit, stop command, and message chunking.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_telegram_gateway_adapter.py::test_telegram_update_maps_to_message_event`.
- [ ] Run `python -m pytest tests/gateway/test_telegram_gateway_adapter.py::test_telegram_update_maps_to_message_event -q` and confirm failure.
- [ ] Implement update parsing, outbound send/edit, chunking, and dry-run setup.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for bot token redaction, topic routing, oversized messages, retryable API errors, and `/stop`.
- [ ] Run `python -m pytest tests/gateway/test_telegram_gateway_adapter.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add telegram gateway adapter`.

## Verification

```powershell
python -m pytest tests/gateway/test_telegram_gateway_adapter.py -q
pf-agent gateway telegram check --dry-run
python -m pytest -q
```

## Acceptance

- Telegram behavior is tested through fake HTTP only.
- Oversized responses are split without losing final delivery state.
- Token and chat identifiers are redacted in diagnostics.
- The adapter remains optional when Telegram dependencies are absent.

## Commit Boundary

Commit only Task 157 Telegram adapter files, tests, fixtures, and required CLI wiring. Do not bundle adjacent task cards.

