# Task 161: Gateway Delivery Reliability

## Goal

Make gateway delivery reliable through chunking, retries, continuation tracking, and final-delivery accounting.

## Architecture Notes

Delivery reliability is shared by all platform adapters. Adapters report platform limits and results; the gateway delivery layer handles retries, backoff, continuation ids, and final state.

## Files

- Create `src/proseforge_agent/gateway/delivery.py`.
- Extend `src/proseforge_agent/gateway/platforms/base.py`.
- Add tests in `tests/gateway/test_gateway_delivery_reliability.py`.

## Interfaces / Contracts

- `DeliveryManager.deliver(session_key, outbound_message) -> DeliveryResult`.
- `DeliveryResult` records final delivered status, continuation ids, retry count, and sanitized errors.
- Chunking obeys platform max text size and preserves order.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_gateway_delivery_reliability.py::test_chunked_delivery_requires_all_continuations`.
- [ ] Run `python -m pytest tests/gateway/test_gateway_delivery_reliability.py::test_chunked_delivery_requires_all_continuations -q` and confirm failure.
- [ ] Implement delivery manager, chunking, retry/backoff, and final-delivery accounting.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for partial continuation failure, retry exhaustion, duplicate suppression, and adapter-specific limits.
- [ ] Run `python -m pytest tests/gateway/test_gateway_delivery_reliability.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add gateway delivery reliability`.

## Verification

```powershell
python -m pytest tests/gateway/test_gateway_delivery_reliability.py -q
pf-agent gateway delivery check --provider fake
python -m pytest -q
```

## Acceptance

- A message is marked delivered only when every required chunk lands.
- Retryable errors are retried within configured limits.
- Duplicate delivery is prevented after restart recovery.
- Delivery records are safe for support bundles.

## Commit Boundary

Commit only Task 161 delivery, adapter contract updates, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

