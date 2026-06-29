# Task 159: WhatsApp Signal Email Gateway Adapters

## Goal

Add optional WhatsApp, Signal, and Email gateway adapters for non-desktop remote use.

## Architecture Notes

These adapters are optional and dependency-gated. The core product must still work when no mobile or email platform dependency is installed.

## Files

- Create `src/proseforge_agent/gateway/platforms/whatsapp.py`.
- Create `src/proseforge_agent/gateway/platforms/signal.py`.
- Create `src/proseforge_agent/gateway/platforms/email.py`.
- Add tests in `tests/gateway/test_mobile_email_gateway_adapters.py`.

## Interfaces / Contracts

- `pf-agent gateway whatsapp check --dry-run`
- `pf-agent gateway signal check --dry-run`
- `pf-agent gateway email check --dry-run`
- Adapters normalize text, sender id, thread id, attachments, and delivery receipts.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_mobile_email_gateway_adapters.py::test_mobile_email_adapters_normalize_events`.
- [ ] Run `python -m pytest tests/gateway/test_mobile_email_gateway_adapters.py::test_mobile_email_adapters_normalize_events -q` and confirm failure.
- [ ] Implement optional adapters with fake clients and shared normalization.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for attachment metadata, dependency missing mode, address redaction, delivery retry, and unsubscribe/stop.
- [ ] Run `python -m pytest tests/gateway/test_mobile_email_gateway_adapters.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add mobile and email gateway adapters`.

## Verification

```powershell
python -m pytest tests/gateway/test_mobile_email_gateway_adapters.py -q
pf-agent gateway email check --dry-run
python -m pytest -q
```

## Acceptance

- Each adapter is optional and testable without real accounts.
- Sender identifiers and secrets are redacted in diagnostics.
- Attachments are passed as metadata and content references, not raw unbounded blobs.
- Unsupported platform capabilities degrade clearly.

## Commit Boundary

Commit only Task 159 adapter files, tests, fixtures, and required CLI wiring. Do not bundle adjacent task cards.

