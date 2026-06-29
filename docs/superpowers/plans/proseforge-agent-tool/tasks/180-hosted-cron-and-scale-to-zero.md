# Task 180: Hosted Cron And Scale To Zero

## Goal

Add hosted cron contracts and scale-to-zero lifecycle support for unattended non-desktop agent jobs.

## Architecture Notes

The local scheduler remains useful, but hosted cron separates trigger ownership from the sleeping agent. Inbound cron fires must be authenticated, scoped, idempotent, and recoverable.

## Files

- Create `src/proseforge_agent/cron/`.
- Add tests in `tests/cron/test_hosted_cron_scale_to_zero.py`.
- Add fixtures under `tests/cron/fixtures/hosted-cron/`.

## Interfaces / Contracts

- `pf-agent cron add "daily report" --schedule "0 9 * * *" --dry-run`
- `pf-agent cron fire --fixture demo --provider fake`
- Cron fire payloads include job id, schedule id, nonce, issued_at, expiration, and signature metadata.

## TDD Steps

- [ ] Write failing test `tests/cron/test_hosted_cron_scale_to_zero.py::test_cron_fire_requires_valid_audience_and_nonce`.
- [ ] Run `python -m pytest tests/cron/test_hosted_cron_scale_to_zero.py::test_cron_fire_requires_valid_audience_and_nonce -q` and confirm failure.
- [ ] Implement cron job model, hosted fire verifier, idempotency store, lifecycle states, and dry-run CLI.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for expired fire, duplicate nonce, scale-to-zero wake plan, local fallback, and delivery target.
- [ ] Run `python -m pytest tests/cron/test_hosted_cron_scale_to_zero.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add hosted cron and scale to zero`.

## Verification

```powershell
python -m pytest tests/cron/test_hosted_cron_scale_to_zero.py -q
pf-agent cron add "daily report" --schedule "0 9 * * *" --dry-run
python -m pytest -q
```

## Acceptance

- Hosted cron fires are authenticated and idempotent.
- The agent can plan wake, run, deliver, and hibernate lifecycle states.
- Local scheduler fallback remains available.
- Dry-run mode requires no external hosted service.

## Commit Boundary

Commit only Task 180 cron files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

