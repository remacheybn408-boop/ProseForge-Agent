# Task 158: Discord And Slack Gateway Adapters

## Goal

Add Discord and Slack gateway adapters behind the shared platform contract.

## Architecture Notes

Discord and Slack share thread/channel concepts but differ in auth and delivery limits. Keep shared formatting helpers separate from platform-specific clients.

## Files

- Create `src/proseforge_agent/gateway/platforms/discord.py`.
- Create `src/proseforge_agent/gateway/platforms/slack.py`.
- Add tests in `tests/gateway/test_discord_slack_gateway_adapters.py`.

## Interfaces / Contracts

- `pf-agent gateway discord check --dry-run`
- `pf-agent gateway slack check --dry-run`
- Both adapters support inbound messages, thread ids, outbound replies, edits where supported, and stop/interrupt commands.

## TDD Steps

- [ ] Write failing test `tests/gateway/test_discord_slack_gateway_adapters.py::test_discord_and_slack_events_share_contract`.
- [ ] Run `python -m pytest tests/gateway/test_discord_slack_gateway_adapters.py::test_discord_and_slack_events_share_contract -q` and confirm failure.
- [ ] Implement fake-client adapters, shared formatting helpers, auth redaction, and dry-run checks.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for threads, role authorization, rate limits, unsupported edits, and delivery retries.
- [ ] Run `python -m pytest tests/gateway/test_discord_slack_gateway_adapters.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add discord and slack gateway adapters`.

## Verification

```powershell
python -m pytest tests/gateway/test_discord_slack_gateway_adapters.py -q
pf-agent gateway discord check --dry-run
pf-agent gateway slack check --dry-run
python -m pytest -q
```

## Acceptance

- Discord and Slack adapters use the same gateway event contract.
- Platform credentials are never printed.
- Thread routing is deterministic.
- Missing optional dependencies degrade to clear doctor warnings.

## Commit Boundary

Commit only Task 158 adapter files, tests, fixtures, and required CLI wiring. Do not bundle adjacent task cards.

