# ProseForge Agent

An agentic orchestration layer for long-form novel production. It wraps the
existing **ProseForge engine** (the canonical writing engine) with planning,
retrieval, drafting, review, revision, deep memory, multi-provider model
routing, daily workbooks, reports, extensions, and release checks.

ProseForge Agent does **not** reimplement the writing engine. The engine at
`$PROSEFORGE_ROOT` remains the source of truth for project slots, pipeline
actions, guards, reports, and exports. This package owns orchestration:
model calls, provider routing, schedules, evidence packs, agent memory, and
workflow state.

## Status

Active implementation. The package now includes the CLI shell, configuration
loading, workspace helpers, ProseForge engine adapter, provider registry and
profiles, retrieval evidence packs, memory ingestion and compaction, phase
planning, daily workbook generation, chapter lifecycle workflows, reports,
extension hooks, an end-to-end demo, and release checks.

Several CLI command groups are present as operator-facing entry points. Some
groups still return planned reports until their deeper integrations are wired.
Provider inspection and command-reference reporting are implemented.

## Requirements

- Python 3.10+
- `pyyaml>=6.0`
- `pytest>=7.0` for development and test runs

## Layout

```text
src/proseforge_agent/       importable package (src-layout)
  cli.py                    pf-agent command entry point
  config.py                 YAML config loading and validation
  workspace.py              project workspace helpers
  proseforge/               adapter boundary for the ProseForge engine
  llm/                      provider contracts, registry, HTTP helpers
  llm/providers/            native provider profiles and adapters
  retrieval/                indexes, routing, and evidence packs
  memory/                   durable memory schema, store, ingestion, compaction
  planning/                 intake parsing and phase plan generation
  daily/                    daily workbook and recommendations
  chapter/                  context, draft, review, rewrite, accept lifecycle
  workflow/                 workflow state and recovery
  reports/                  Markdown, JSON, and terminal report rendering
  extensions/               extension registry and hook base classes
configs/                    agent and provider example configs
docs/                       operator, developer, and implementation docs
samples/                    sample extensions
tests/                      pytest suite and provider fixtures
```

## Development

Run the tests. No install is required because `pythonpath` is configured in
`pyproject.toml`:

```powershell
python -m pytest -q
```

Invoke the CLI directly:

```powershell
python -m proseforge_agent.cli --help
```

After an editable install, the `pf-agent` command is available on the path:

```powershell
python -m pip install -e ".[dev]"
pf-agent --help
```

Render the command reference:

```powershell
python -m proseforge_agent.cli report command-reference --format terminal
```

Inspect provider routing with the offline fake-provider example:

```powershell
python -m proseforge_agent.cli provider --providers configs/providers.example.yaml
```

## Provider Profiles

Provider profiles live under `configs/providers/`, with matching adapters and
tests under `src/proseforge_agent/llm/providers/` and `tests/`. Current profiles
include OpenAI, Anthropic, Gemini, xAI/Grok, DeepSeek, Qwen, GLM, Mimo,
MiniMax, and Doubao.

Keep secrets in environment variables or local ignored config files. Do not
commit API keys into provider YAML.

## ProseForge Engine Boundary

Set `PROSEFORGE_ROOT` when commands need to discover or call the canonical
ProseForge engine. This repository remains the orchestration layer and should
avoid duplicating engine-owned project, pipeline, guard, export, or report
logic.
