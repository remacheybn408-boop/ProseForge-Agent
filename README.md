# ProseForge Agent

An agentic orchestration layer for long-form novel production. It wraps the
existing **ProseForge engine** (the canonical writing engine) with planning,
retrieval, drafting, review, revision, deep memory, multi-provider model
routing, daily workbooks, and export workflows.

ProseForge Agent does **not** reimplement the writing engine. The engine at
`$PROSEFORGE_ROOT` remains the source of truth for project slots, pipeline
actions, guards, reports, and exports. This package owns orchestration:
model calls, provider routing, schedules, evidence packs, agent memory, and
workflow state.

## Status

Early skeleton. This is Task 01 (package skeleton) of the implementation plan
in `docs/superpowers/plans/proseforge-agent-tool/`. Only the importable
package, typed errors, and the CLI shell exist so far.

## Requirements

- Python 3.10+

## Layout

```text
src/proseforge_agent/   importable package (src-layout)
  __init__.py           package metadata and __version__
  errors.py             typed exception hierarchy
  cli.py                pf-agent command entry point
tests/                  pytest suite
```

## Development

Run the tests (no install required — `pythonpath` is configured in
`pyproject.toml`):

```powershell
python -m pytest -q
```

Invoke the CLI directly:

```powershell
python -m proseforge_agent.cli --help
```

After an editable install (`pip install -e .`) the `pf-agent` command is also
available on the path.
