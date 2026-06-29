# Task 152: Slash Command Registry

## Goal

Add a shared slash-command registry for CLI, TUI, and gateway surfaces.

## Architecture Notes

Slash commands are intent adapters, not privileged bypasses. They call existing session, model, tool, profile, and workflow services under the same permission ceiling as normal chat.

## Files

- Create or extend `src/proseforge_agent/chat/slash.py`.
- Add tests in `tests/chat/test_slash_command_registry.py`.
- Update CLI/TUI/gateway wiring only where needed.

## Interfaces / Contracts

- Commands include `/new`, `/reset`, `/retry`, `/undo`, `/compress`, `/usage`, `/model`, `/mode`, `/project`, `/skills`, and `/help`.
- `SlashCommandRegistry.resolve(text, context)` returns a typed action or `None`.
- Unknown commands return a helpful error without model calls.

## TDD Steps

- [ ] Write failing test `tests/chat/test_slash_command_registry.py::test_registry_resolves_builtin_command`.
- [ ] Run `python -m pytest tests/chat/test_slash_command_registry.py::test_registry_resolves_builtin_command -q` and confirm failure.
- [ ] Implement command registration, parsing, aliases, help text, and permission checks.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for unknown commands, permission denial, aliases, and command help.
- [ ] Run `python -m pytest tests/chat/test_slash_command_registry.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add slash command registry`.

## Verification

```powershell
python -m pytest tests/chat/test_slash_command_registry.py -q
pf-agent chat --message "/help" --provider fake --no-project
python -m pytest -q
```

## Acceptance

- Slash commands behave consistently across interactive surfaces.
- Commands cannot raise permissions or bypass approvals.
- Help output is deterministic and testable.
- Existing chat message handling remains compatible.

## Commit Boundary

Commit only Task 152 command registry files, tests, fixtures, and minimal wiring. Do not bundle adjacent task cards.

