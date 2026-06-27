# ProseForge Agent — Operator Quickstart

ProseForge Agent is an orchestration layer that drives the existing **ProseForge
engine** through a daily novel-production workflow (planning, drafting, review,
memory, retrieval, export). The Agent *orchestrates* the engine; it never copies
or modifies engine code.

## Install

```powershell
pip install -e .
pf-agent --help
```

`pf-agent --help` lists every command group. For a full, self-describing
reference:

```powershell
pf-agent report command-reference --write
```

## Two roots: keep them separate

The Agent works with **two independent directories**. Understanding the split is
the single most important setup concept.

### 1. `$PROSEFORGE_ROOT` — the engine you already have

This is your existing ProseForge engine checkout. The Agent reads it through the
engine adapter and never writes into it except via the engine's own scripts.

```
$PROSEFORGE_ROOT/
|- plugin/proseforge-codex/scripts/nf_project.py    project actions
|- plugin/proseforge-codex/scripts/nf_pipeline.py   pipeline actions (post, review, export)
|- workspace/<slot>/novel.db                          engine-owned manuscript DB
|- exports/                                            engine exports
`- reports/                                            engine reports
```

### 2. The Agent workspace — everything the Agent owns

Separate, Agent-owned state. Default location `.pf-agent` (override with
`PROSEFORGE_AGENT_WORKSPACE`). The Agent never stores its state inside
`$PROSEFORGE_ROOT`.

```
<workspace_root>/            # default .pf-agent
|- projects/                  per-project state
|- phase_plans/               generated phase plans
|- daily_workbooks/           dated workbooks
|- evidence_packs/            retrieved context bundles
|- workflow_runs/             resumable chapter run state (JSON per run)
|- drafts/  prompts/  reports/  logs/
`- agent.db                   Agent SQLite memory store
```

## Configuration

Configuration is portable — no machine-specific absolute paths. The two roots
are injected from environment variables (see `configs/agent.example.yaml`):

```yaml
paths:
  proseforge_root: "${PROSEFORGE_ROOT}"
  workspace_root: "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}"
```

Set `PROSEFORGE_ROOT` to your engine checkout; the workspace defaults to a local
`.pf-agent` folder you can relocate freely. Relative paths in the config resolve
from the directory that contains the config file.

## Where to go next

- Command groups: `project`, `proseforge`, `provider`, `memory`, `retrieve`,
  `phase-plan`, `daily-workbook`, `chapter`, `workflow`, `report`, `extension`.
- Extending the Agent: see `docs/developer-extensions.md`.
