# Task 179: User Model And Memory Nudges

## Goal

Add a user model and periodic memory nudges that help the agent preserve useful preferences without silently canonizing them.

## Architecture Notes

This extends memory candidates. The user model stores explicit, reviewable preference and working-style facts. Nudges ask whether a pattern should become memory; they do not write accepted canon automatically.

## Files

- Create `src/proseforge_agent/memory/user_model.py`.
- Create `src/proseforge_agent/memory/nudges.py`.
- Add tests in `tests/memory/test_user_model_memory_nudges.py`.

## Interfaces / Contracts

- `UserModelFact` includes scope, confidence, source refs, status, and last_confirmed_at.
- `MemoryNudge` includes candidate id, reason, suggested scope, and action choices.
- `pf-agent memory nudges --provider fake`.

## TDD Steps

- [ ] Write failing test `tests/memory/test_user_model_memory_nudges.py::test_nudge_does_not_accept_memory_automatically`.
- [ ] Run `python -m pytest tests/memory/test_user_model_memory_nudges.py::test_nudge_does_not_accept_memory_automatically -q` and confirm failure.
- [ ] Implement user model facts, nudge generation, candidate links, and CLI display.
- [ ] Run the targeted test and confirm pass.
- [ ] Add companion tests for global/project scope, stale facts, contradiction candidates, rejection, and redaction.
- [ ] Run `python -m pytest tests/memory/test_user_model_memory_nudges.py -q` and `python -m pytest -q`.
- [ ] Commit with `feat: add user model and memory nudges`.

## Verification

```powershell
python -m pytest tests/memory/test_user_model_memory_nudges.py -q
pf-agent memory nudges --provider fake
python -m pytest -q
```

## Acceptance

- User preferences are reviewable memory candidates or facts.
- Nudges never accept canon automatically.
- Global and project scopes remain separate.
- Contradictions are surfaced instead of overwritten silently.

## Commit Boundary

Commit only Task 179 memory user model/nudge files, tests, fixtures, and CLI wiring. Do not bundle adjacent task cards.

