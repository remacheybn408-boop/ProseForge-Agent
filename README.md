# ProseForge Agent

An agentic orchestration layer for long-form novel production. It wraps the
existing **ProseForge engine** (the canonical writing engine) with planning,
retrieval, drafting, review, revision, deep memory, multi-provider model
routing, daily workbooks, reports, extensions, an agent runtime, chat, an
autonomous goal-directed loop, usage metering, streaming, safety guards,
capability flags, and release checks.

ProseForge Agent does **not** reimplement the writing engine. The engine at
`$PROSEFORGE_ROOT` remains the source of truth for project slots, pipeline
actions, guards, reports, and exports. This package owns orchestration:
model calls, provider routing, schedules, evidence packs, agent memory,
workflow state, conversational agent loop, and background event processing.

## Status

**712 tests passing.** The implementation covers task cards 1–100 of the
project plan — the full core, provider, agent runtime, and chat stack
(1–60), the hardening cards (61–67), the autonomous runtime cards (68–70),
and the agent-expansion, guided-setup, novel-operations, story-intelligence,
and editorial tracks (71–100).

**Core layer** — config, workspace, ProseForge engine adapter, provider
registry (10 provider profiles), retrieval evidence packs, memory schema
and store with ingestion and compaction, phase planning, daily workbook
generation, chapter lifecycle (draft → review → rewrite → accept),
workflow state with recovery, CLI with report rendering, extension hooks,
end-to-end demo, and release checks.

**Agent Runtime** — per-turn AgentKernel with dependency-injected provider,
tools, session store, retrieval, and intent router; conversation modes and
permission policy; tool registry with capability-based access control.

**Chat** — session store with transcript persistence, interactive CLI REPL,
prompt protocol, retrieval with cited evidence packs, memory-backed user
preferences, chat-to-workflow handoff, and agent event bus for background
jobs with progress tracking.

**Native install** — cross-platform app directories, installation doctor,
first-run onboarding, native secret storage, provider setup wizard,
pip/pipx/source and standalone-binary packaging, Windows/macOS/Linux native
support, shell completions, upgrade/migration/backup, uninstall, offline
local models, a local agent service API, and a cross-platform native QA matrix.

**Hardening (61–67)** — provider usage metering and budgets, an agent
safety / prompt-injection guard, streaming responses, a cross-platform CI
pipeline (validated against the QA matrix), concurrency and advisory file
locking, capability flags with safe-mode boot, and a shared
contract/golden regression-test tier built on canonical fakes.

**Autonomous runtime (68–70)** — a bounded autonomous agent loop
(plan → act → verify → reflect → repeat), a task planner with
dependency-aware TODO tracking, and self-verification with bounded
reflection (pluggable domain verifiers such as the ProseForge review gate).

**Agent tooling (71–75)** — a general tool framework (filesystem and web
tools), a tool execution sandbox, sub-agent delegation, interruptibility and
steering, and an agent evaluation harness.

**Guided setup (76–80)** — the `pf-agent setup` guided installation wizard,
multiple setup modes, a config generator, setup recovery, and first-run
bootstrap.

**Novel project operations (81–87)** — a novel project manifest, an artifact
graph, bulk import, scene-level workflow, chapter reorganization, an
export/compilation pipeline, and publishing metadata.

**Canon and story intelligence (88–94)** — a canon bible manager, a
continuity conflict resolver, a timeline engine, a plot-thread manager, a
foreshadowing tracker, a character-arc tracker, and a relationship graph.

**Writing quality and editorial systems (95–100)** — a writing domain tools
registry, explicit writing rules, a tone/style profile compiler, writing
quality gates, a literary regression suite, and a rewrite strategy library
(nine selectable strategies producing per-strategy revision artifacts).

**Release gate** — automated checks for provider certification, memory audit
enforcement, docs and examples presence, and offline fake-provider demo.

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
  capabilities.py           capability flags and safe-mode boot
  concurrency.py            cross-platform advisory file lock + sqlite retry
  errors.py                 typed exception hierarchy
  proseforge/               adapter boundary for the ProseForge engine
  llm/                      provider contracts, registry, HTTP helpers
  llm/providers/            native provider profiles and adapters
  llm/usage.py              token/cost metering, budgets, rate-limit backoff
  llm/streaming.py          uniform streaming channel with fallback wrapper
  retrieval/                indexes, routing, and evidence packs
  memory/                   durable memory schema, store, ingestion, compaction
  planning/                 intake parsing and phase plan generation
  daily/                    daily workbook and recommendations
  chapter/                  context, draft, review, rewrite, accept lifecycle
  workflow/                 workflow state and recovery
  reports/                  Markdown, JSON, and terminal report rendering
  extensions/               extension registry and hook base classes
  agent/                    kernel, intent router, modes, tools, permissions, events
  agent/safety.py           prompt-injection / permission-escalation guard
  agent/loop.py             bounded autonomous agent loop
  agent/planner.py          task planner and TODO tracking
  agent/reflection.py       self-verification and bounded reflection
  chat/                     session store, repl, prompts, retrieval, memory, handoff
  install/                  app dirs, doctor, packaging, native OS support, QA matrix
  testing/                  canonical fakes shared by contract/golden tests
configs/                    agent and provider example configs
docs/                       operator, developer, and implementation docs
samples/                    sample extensions
tests/                      pytest suite, contract/golden tiers, and fixtures
.github/workflows/ci.yml    cross-platform CI (Windows, macOS, Linux)
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

Launch the interactive chat REPL (add `--stream` for incremental output):

```powershell
python -m proseforge_agent.chat.repl
```

Run an autonomous, goal-directed loop (offline fake provider). Add `--verify`
to self-check each output and reflect/retry on failure, or `--show-plan` to
preview the decomposed task plan:

```powershell
python -m proseforge_agent.cli run --goal "draft a one-line opening" --provider fake --max-iterations 5
python -m proseforge_agent.cli run --goal "写满 200 字的开头" --provider fake --verify
```

List the rewrite strategy library, or apply a strategy to produce a
per-strategy revision artifact for a chapter:

```powershell
python -m proseforge_agent.cli rewrite strategies list
python -m proseforge_agent.cli rewrite --slug my-novel --strategy condense --chapter ch_001
```

Inspect resolved capabilities and safe-mode status:

```powershell
python -m proseforge_agent.cli status --capabilities
```

Report metered provider usage, or validate the CI matrix against the QA matrix:

```powershell
python -m proseforge_agent.cli usage report --since today
python -m proseforge_agent.cli qa ci --check
```

Run the end-to-end offline demo:

```powershell
python -m proseforge_agent.demo
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
