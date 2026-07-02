# Contributing to ProseForge Agent

Thanks for contributing. This project is built one reviewable task card at a
time, test-first. Read this before opening a PR.

## Local Setup

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

No install is strictly required — `pythonpath = ["src"]` is set in
`pyproject.toml`, so `python -m pytest -q` works from a fresh checkout.
The full suite is offline and needs no credentials.

## Branch Strategy

One feature branch per task card, named `feat/task-<N>-<slug>`
(for example `feat/task-186-default-chat-repl-on-bare-command`). Task cards
live in `docs/superpowers/plans/proseforge-agent-tool/tasks/`. Branch from an
up-to-date `main`, and merge back with `--no-ff` so each card is one
reviewable merge commit.

## TDD Requirement

Every card is red → green → refactor:

1. Write the failing test named in the card's TDD Step 1 first.
2. Run it and confirm it fails for the expected reason.
3. Implement the minimum production code to make it pass.
4. Run the card's targeted tests, then the full suite `python -m pytest -q`.

Tests live under `tests/`; a test module name matches the card slug, and the
first assertion targets the behavior named in the card.

## Commit Messages

- `feat: add <slug>` for features, `fix: <slug>` for fixes,
  `docs: <slug>` for docs, `chore: <slug>` for tooling.
- For AI-assisted commits, end with a `Co-Authored-By:` trailer.
- Keep each commit scoped to a single task card (its "Commit Boundary").

## PR Checklist

- [ ] The card's targeted tests pass.
- [ ] The full suite `python -m pytest -q` is green on the feature branch.
- [ ] Merged to `main` with `--no-ff`; the suite is green again after merge.
- [ ] No unrelated task cards bundled into the commit.
- [ ] Secrets are never committed (see `.gitignore` and `.env.example`).

See `AGENTS.md` for conventions that apply to both human and AI contributors.
