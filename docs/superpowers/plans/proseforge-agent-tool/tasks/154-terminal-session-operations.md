# Task 154: Terminal Session Operations

## Goal

Add terminal session operations for retry, undo, compress, usage, and resume.

## Architecture Notes

These operations extend the chat session store and transcript model. They must preserve auditability by soft-deleting or superseding turns instead of destroying history silently.

## Files

- Extend `src/proseforge_agent/chat/session.py` and `src/proseforge_agent/chat/transcript.py`.
- Add terminal command wiring under `src/proseforge_agent/tui/`.
- Add tests in `tests/chat/test_terminal_session_operations.py`.

## Interfaces / Contracts

- `/retry`, `/undo`, `/compress`, `/usage`, `/resume <session-id>`.
- `ChatSessionStore.rewind(...)` records reversible transcript metadata.
- Compression writes a new summary message with evidence of source turns.

## TDD Steps

- [ ] Write failing test `tests/chat/test_terminal_session_operations.py::test_undo_soft_deletes_last_turn`.
- [ ] Run `python -m pytest tests/chat/test_terminal_session_operations.py::test_undo_soft_deletes_last_turn -q` and confirm failure.
- [ ] Implement rewind, retry, compression summary, usage readout, and resume lookup.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for audit trail, empty transcripts, invalid resume ids, and permission-safe compression.
- [ ] Run `python -m pytest tests/chat/test_terminal_session_operations.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add terminal session operations`.

## Verification

```powershell
python -m pytest tests/chat/test_terminal_session_operations.py -q
pf-agent chat --message "/usage" --provider fake --no-project
python -m pytest -q
```

## Acceptance

- Retry and undo are visible in transcript history.
- Compression never drops source references.
- Usage can be shown without a provider call.
- Operations work in CLI and TUI through the same command registry.

## Commit Boundary

Commit only Task 154 session, transcript, terminal wiring, tests, and fixtures. Do not bundle adjacent task cards.

