# Task 151: Terminal UI Foundation

## Goal

Add a Hermes-class non-desktop terminal UI foundation for long-running chat and agent runs.

## Architecture Notes

The TUI is a surface over the existing chat session store, event bus, kernel, and permission policy. It must not become a second agent runtime and must not introduce desktop, Electron, or GUI automation dependencies.

## Files

- Create implementation under `src/proseforge_agent/tui/`.
- Add tests in `tests/tui/test_terminal_ui_foundation.py`.
- Add deterministic fixtures under `tests/tui/fixtures/terminal-ui-foundation/` only if needed.

## Interfaces / Contracts

- `pf-agent tui --provider fake --no-project`
- `TerminalApp.start()` accepts injected input/output streams for tests.
- The TUI renders chat history, current mode, provider, project binding, and running status.

## TDD Steps

- [ ] Write failing test `tests/tui/test_terminal_ui_foundation.py::test_terminal_app_renders_initial_state`.
- [ ] Run `python -m pytest tests/tui/test_terminal_ui_foundation.py::test_terminal_app_renders_initial_state -q` and confirm failure.
- [ ] Implement the smallest TUI shell that renders deterministic state from injected dependencies.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for no-project mode, project-bound mode, provider display, and graceful EOF.
- [ ] Run `python -m pytest tests/tui -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add terminal ui foundation`.

## Verification

```powershell
python -m pytest tests/tui/test_terminal_ui_foundation.py -q
pf-agent tui --provider fake --no-project --check
python -m pytest -q
```

## Acceptance

- The TUI can start in a deterministic fake-provider check mode.
- It shows state without mutating projects, secrets, or global config.
- It reuses chat/session/kernel services through injection.
- No desktop UI or OS GUI automation is introduced.

## Commit Boundary

Commit only Task 151 implementation files, tests, fixtures, and required CLI wiring. Do not bundle adjacent task cards.

