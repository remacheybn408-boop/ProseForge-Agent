# AGENTS.md

Conventions for coding agents (and humans) working in this repository.

## Repo Layout

- `src/proseforge_agent/` — the importable package (src-layout). Subpackages:
  `agent/`, `chat/`, `llm/`, `memory/`, `retrieval/`, `mcp/`, `gateway/`,
  `environments/`, `skills/`, `cron/`, `eval/`, `install/`, `release/`, etc.
- `tests/` — pytest suite; test module names match task-card slugs.
- `docs/superpowers/plans/proseforge-agent-tool/tasks/` — the task cards that
  drive all work.

## Coding Conventions

- `from __future__ import annotations` at the top of every module.
- Value objects are `@dataclass(frozen=True)`; mutable state uses plain
  dataclasses.
- Do not use the `logging` module for agent events — emit through `EventBus`
  / `ObserverRegistry` in `agent/`.
- Providers, transports, and runners are dependency-injected so tests stay
  offline; never hard-code a network client.

## Test Conventions

- Tests live under `tests/`; the module name matches the card slug.
- The first assertion targets the RED behavior named in the card.
- Run the whole suite with `python -m pytest -q` before every commit and
  after every `--no-ff` merge to `main`.

## Forbidden Actions

- Never write to `$PROSEFORGE_ROOT` from this repository.
- Never bypass `PermissionPolicy` or the MCP approval gate.
- Never log or export secret material (respect the redaction helpers).
- Never add a runtime dependency that is not already in `pyproject.toml`.
- Never commit `.env` / secrets; only `.env.example` is tracked.

## Where To Look

- Task cards and their commit boundaries: the tasks directory above.
- Contribution workflow and commit-message shape: `CONTRIBUTING.md`.
- Security scope and reporting: `SECURITY.md`.
