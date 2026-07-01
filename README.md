# ProseForge Agent

An agentic orchestration layer for long-form novel production. It wraps the
canonical **ProseForge engine** (`$PROSEFORGE_ROOT`) with planning, retrieval,
drafting, review, revision, deep memory, multi-provider model routing, daily
workbooks, reports, extensions, an agent runtime, chat, an autonomous
goal-directed loop, MCP integration, execution environments, skills, hosted
cron, observability, middleware, and a real publish/binary/installer chain.

ProseForge Agent does **not** reimplement the writing engine. The engine at
`$PROSEFORGE_ROOT` remains the source of truth for project slots, pipeline
actions, guards, reports, and exports. This package owns orchestration:
model calls, provider routing, schedules, evidence packs, agent memory,
workflow state, conversational agent loop, and background event processing.

## Status

**1035 tests passing** on Python 3.10/3.11 across Windows, macOS, and Linux.
The implementation covers task cards **1–185** of the project plan — the full
core stack, agent runtime, chat, native install, hardening, autonomous
runtime, agent tooling, guided setup, novel operations, canon and story
intelligence, editorial systems, the MCP integration track, provider/tool
resilience, RAG, gateway, execution environments, skills, hosted cron,
observability, middleware, and the real release chain.

### Core stack (1–17)

Portable config, workspace layout, ProseForge engine adapter, provider
contract + fake provider, OpenAI-compatible transport, native/local
provider profiles, memory schema/store with ingestion + compaction,
retrieval router and evidence packs, phase plan generator, daily workbook
engine, workflow state and recovery, chapter lifecycle
(draft → review → rewrite → accept), CLI commands and reports, extensions,
and an end-to-end demo with release checks.

### Provider registry (18–30)

Ten native provider profiles — **OpenAI, Anthropic, Gemini, xAI/Grok,
DeepSeek, Qwen, GLM, Mimo, MiniMax, Doubao** — plus capability probing,
provider fallback router, and a provider certification workflow. All
providers go through a shared `HttpTransport` (`urllib`-backed in
production, `FakeHttpTransport` in tests), so no test hits the network.

### Agent runtime & chat (33–40)

`AgentKernel` with dependency-injected provider, tools, session store,
retrieval, and intent router; conversation modes; permission policy; tool
registry with capability-based access; chat session store, prompt protocol,
retrieval-cited evidence, chat-to-workflow handoff, and an agent event bus
for background jobs with progress tracking.

### Native install & distribution (41–58)

Cross-platform app directories, installation doctor, first-run onboarding,
native secret storage, provider setup wizard, pip/pipx/source and
standalone-binary packaging manifest, Windows/macOS/Linux native support
checks, shell completions, upgrade/migration/backup, uninstall,
offline local model setup, a local agent service API, agent profiles, and
a cross-platform native QA matrix.

### Hardening & release gates (61–67)

Provider usage metering + budgets, an agent safety / prompt-injection
guard, streaming responses, a cross-platform CI pipeline, concurrency +
advisory file locking, capability flags with safe-mode boot, and a
contract/golden regression tier built on canonical fakes.

### Autonomous runtime & agent tooling (68–75)

A bounded autonomous loop (plan → act → verify → reflect → repeat), task
planner with dependency-aware TODOs, self-verification with bounded
reflection (pluggable domain verifiers such as the ProseForge review
gate), a general tool framework (`fs.read/write/edit`, `web.fetch/search`),
tool execution sandbox, sub-agent delegation, interruptibility + steering,
and an agent evaluation harness.

### Guided setup & novel operations (76–87)

Guided `pf-agent setup` wizard, multiple setup modes, config generator,
setup recovery, first-run bootstrap, novel project manifest, artifact
graph, bulk import, scene-level workflow, chapter reorganization,
export/compilation pipeline, and publishing metadata.

### Canon & story intelligence (88–94)

Canon bible manager, continuity conflict resolver, timeline engine,
plot-thread manager, foreshadowing tracker, character-arc tracker, and
relationship graph.

### Writing quality & editorial (95–108)

Writing domain tools registry, explicit writing rules, tone/style profile
compiler, quality gates, literary regression suite, rewrite strategy
library (nine selectable strategies), reader-experience review,
whole-manuscript search, project health doctor, draft versioning with
diff/branch/approval-gated rollback, a staged editorial pipeline
(outline → … → final), human approval queue, writing analytics with
completion prediction, and checksum-verified backups with dry-run restore.

### Agent protocol, prompt, context, audit (109–115)

Structured function-calling adapter, structured-output repair, context
window management with compaction, system-prompt management, prompt
template registry, multimodal / attachment ingestion (PDF, DOCX, CSV,
Markdown, TXT, image metadata + vision describer), and an audit trail
with deterministic replay.

### MCP integration (116–121)

MCP client foundation (`stdio` and HTTP/SSE transports with
`StaticMCPTransport` for tests), server registry, security boundary, tool
approval gate, tool schema validation, and credentials boundary. Real
process/network transports are pluggable at call time; test suites use
the deterministic in-process transport.

### Provider & tool resilience (122–126)

Tool timeout / rate limit / circuit breaker, provider fallback, graceful
degradation, offline mode, and a request cache.

### Sessions & context (127–132)

Conversation lifecycle, cross-session search, session export/import,
session branching, session merge, and multi-context switch.

### Retrieval & RAG (133–136, 138–140)

Embeddings abstraction with fake provider, pluggable vector stores,
hybrid retrieval (BM25 + vector), RAG ingestion pipeline, evidence-pack
retrieval, and a RAG evaluation harness.

### Notifications & jobs (137, 141–143)

Notification core, desktop notifications, webhook notifications, and a
job status center.

### Plugins (144–151)

Plugin manifest spec, discovery, install/update/remove CLI, permission
model, sandbox, dependency management, hooks, and a plugin test harness.

### TUI & terminal (152–154)

Terminal UI foundation, slash-command registry, streaming tool output,
and terminal session operations.

### Messaging gateway (155–161)

Messaging gateway core, platform adapter contract, and adapters for
Telegram, Slack, Discord, Signal, mobile e-mail, Email, and a relay
auth + pairing flow. Adapters ship with contract-shaped fake transports;
real transport wiring is per-adapter and read from injected credentials
at call time.

Gateway delivery reliability (retry/backoff/dead-lettering) and media +
voice ingestion round out the gateway track.

### Execution environments (162–168)

Execution environment abstraction, local / Docker / SSH / Singularity /
Modal / Daytona backends, remote file sync and checkpoints, and a
process registry + terminal lifecycle. Backends currently emit
deterministic dry-run plans; the real subprocess invocations are
injectable and wired at call time.

### Managed tool gateway (169–174)

Managed tool gateway foundation, web search and URL safety tools, cloud
browser adapter, media generation and transcription tools, tool result
artifacts + output limits, and the skill specification and registry.

### Skills (175–178)

Skill hub install and sync, autonomous skill creation, skill
self-improvement + provenance tracking, and skill usage analytics + a
safety audit surface.

### Long-lived agents (179–180)

User model + memory nudges, and hosted cron + scale-to-zero lifecycle
support (authenticated + idempotent cron fires, deterministic wake plan,
local fallback).

### Observability & research (181–182)

Observer hooks (read-only) with 7 event families
(`session / turn / provider_request / tool_call / approval / subagent /
job`), correlation-id propagation, fail-open error handling, and a
`pf-agent telemetry export --format jsonl --redact` command. Middleware
hooks (behavior-changing, opt-in, ordered, fail-open) with rewritten
requests re-checked by downstream policy, plus research-ready
`pf-agent trajectories export --redact --format jsonl`.

### Real release chain (183–185)

`PyPIPublisher` — real `python -m build` + `twine upload` for TestPyPI /
PyPI, gated by the Task 47 `PackageChecker` and duplicate-version refusal,
with injectable runner + `dry_run` for offline tests; tokens never appear
in the plan, report, or logs.

`BinaryBuilder` — real PyInstaller invocation derived from the Task 48
`BinaryManifest`, followed by the `pf-agent --version` smoke command as
the gate; portable-path report, `dry_run` for offline tests.

`InstallerBuilder` — per-OS installers (`.msi` via `signtool`, `.dmg` via
`codesign`, `install.sh` via `gpg`), install paths from `AppDirs`,
credential-gated signing that warn-skips when credentials are absent so
an unsigned-but-valid installer is still produced.

## Requirements

- Python **3.10+** (tested on 3.10 and 3.11)
- `pyyaml>=6.0`
- `pytest>=7.0` for development and test runs

Everything else is standard-library only. Providers use `urllib`; MCP,
gateway, and execution backends accept injected clients so no third-party
network dependency is required to run the test suite.

## Layout

```text
src/proseforge_agent/       importable package (src-layout)
  cli.py                    pf-agent command entry point (71 command groups)
  config.py                 YAML config loading and validation
  workspace.py              project workspace helpers
  capabilities.py           capability flags and safe-mode boot
  concurrency.py            cross-platform advisory file lock + sqlite retry
  demo.py                   end-to-end offline demo runner
  errors.py                 typed exception hierarchy

  proseforge/               adapter boundary for the ProseForge engine

  llm/                      provider contracts, registry, HTTP transport,
                            certification, fallback router, streaming,
                            usage metering + budgets
  llm/providers/            10 native provider profiles

  memory/                   schema, store, ingestion, compaction, review,
                            user model + memory nudges
  retrieval/                embeddings, vector store, hybrid retrieval,
                            RAG ingestion, evidence packs, evaluation

  planning/                 intake parsing and phase plan generation
  daily/                    daily workbook and recommendations
  chapter/                  context, draft, review, rewrite, accept lifecycle
  workflow/                 workflow state and recovery
  novel/                    novel project manifest, artifact graph, scene
                            workflow, canon bible, timeline, plot threads,
                            character arcs, style/tone, quality gates,
                            editorial pipeline, backups, approvals
  reports/                  Markdown, JSON, and terminal report rendering
  extensions/               extension registry and hook base classes

  agent/                    kernel, intent router, modes, tools,
                            permissions, events, safety, loop, planner,
                            reflection, sandbox, subagent, profiles,
                            attachments, audit, context window, prompt
                            templates, function calling, structured
                            output repair, provider fallback, degradation,
                            offline, request cache, observability,
                            middleware, execution guard

  chat/                     session store, repl, prompts, retrieval,
                            memory, handoff, lifecycle, cross-session
                            search, export/import, branching, merge,
                            multi-context switch

  mcp/                      client, server registry, schema, policy,
                            approval, credentials

  gateway/                  messaging core, delivery reliability, media/
                            voice ingestion
  gateway/platforms/        Telegram / Slack / Discord / Signal / Email /
                            mobile e-mail adapters
  gateway/relay/            relay auth + pairing

  environments/             execution env abstraction, local / Docker /
                            SSH / Singularity / Modal / Daytona backends,
                            file sync + checkpoints, process registry,
                            serverless

  tools/                    managed tool gateway foundation, web
                            search/URL safety, cloud browser, media gen +
                            transcription, tool result artifacts

  skills/                   skill registry, hub install/sync, autonomous
                            creation, self-improvement, usage analytics,
                            safety audit

  cron/                     hosted cron verification + scale-to-zero plan

  eval/                     trajectory datasets + research-ready export

  notifications/            core, desktop, webhook

  plugins/                  manifest, discovery, permission, sandbox,
                            dependency, hooks, harness

  install/                  app dirs, doctor, package checks, binary
                            packaging manifest, binary_build.py (Task 184),
                            installers.py (Task 185), native OS support

  release/                  release gate, publish.py (Task 183)

  service/                  local agent service API
  setup/                    guided setup wizard, modes, config generator
  tui/                      terminal UI foundation, slash commands,
                            streaming tool output
  testing/                  canonical fakes shared by contract/golden tests

configs/                    agent and provider example configs
docs/                       operator, developer, implementation, and
                            task-card plans (docs/superpowers/plans/)
samples/                    sample extensions
tests/                      pytest suite (1035 tests) + contract / golden
                            tiers + fixtures
.github/workflows/ci.yml    cross-platform CI (Windows, macOS, Linux)
```

## Development

Run the full test suite. No install is required — `pythonpath` is
configured in `pyproject.toml`:

```powershell
python -m pytest -q
```

Invoke the CLI directly:

```powershell
python -m proseforge_agent.cli --help
```

After an editable install, the `pf-agent` command is on your path:

```powershell
python -m pip install -e ".[dev]"
pf-agent --help
```

## CLI Highlights

The `pf-agent` command exposes 71 command groups. Every group shares
`--format` (markdown / json / terminal), `--write`, `--dry-run`, and
`--out` output flags (except a few groups that own their own `--format`,
such as `telemetry` and `trajectories` which emit JSONL).

Render the full command reference:

```powershell
pf-agent report command-reference --format terminal
```

Inspect provider routing with the offline fake provider:

```powershell
pf-agent provider --providers configs/providers.example.yaml
```

Chat REPL (add `--stream` for incremental output):

```powershell
python -m proseforge_agent.chat.repl
pf-agent chat --message "draft an opening" --provider fake
```

Autonomous, goal-directed loop:

```powershell
pf-agent run --goal "draft a one-line opening" --provider fake --max-iterations 5
pf-agent run --goal "写满 200 字的开头" --provider fake --verify
```

Rewrite strategies:

```powershell
pf-agent rewrite strategies list
pf-agent rewrite --slug my-novel --strategy condense --chapter ch_001
```

Novel operations, canon, timeline, plot threads, style/quality gates:

```powershell
pf-agent scene draft --slug my-novel --chapter ch_001 --scene sc_01
pf-agent bible refresh --slug my-novel
pf-agent timeline check --slug my-novel
pf-agent quality report --slug my-novel
```

MCP integration:

```powershell
pf-agent mcp list
pf-agent mcp inspect filesystem
pf-agent mcp tools filesystem
```

Skills:

```powershell
pf-agent skills list
pf-agent skills install <name>
```

Hosted cron + scale-to-zero:

```powershell
pf-agent cron add "daily report" --schedule "0 9 * * *" --dry-run
pf-agent cron fire --fixture demo --provider fake
```

Observability & research exports:

```powershell
pf-agent telemetry export --input .pf-agent/telemetry.jsonl --output out.jsonl --format jsonl --redact
pf-agent trajectories export --input .pf-agent/trajectories.jsonl --output ds.jsonl --format jsonl --redact
```

Health, capabilities, usage, QA:

```powershell
pf-agent doctor
pf-agent status --capabilities
pf-agent usage report --since today
pf-agent qa ci --check
```

End-to-end offline demo:

```powershell
python -m proseforge_agent.demo
```

## Provider Profiles

Provider profiles live under `configs/providers/` with matching adapters
and tests under `src/proseforge_agent/llm/providers/` and `tests/`.
Current profiles: **OpenAI, Anthropic, Gemini, xAI/Grok, DeepSeek, Qwen,
GLM, Mimo, MiniMax, Doubao**.

Keep secrets in environment variables or local ignored config files. Do
not commit API keys into provider YAML.

## What is production-ready and what is contract-only

The project intentionally splits "contract + fake" from "real wiring" so
tests stay deterministic and offline. A few tracks are contract-complete
with fake/dry-run implementations that the operator wires to real
transports at call time:

- **Production ready today** — LLM providers (real HTTP via `urllib`,
  10 profiles), memory (SQLite), workspace + config, planning / daily /
  chapter / workflow, tool registry + permission policy, attachment
  ingestion, embeddings + retrieval + RAG, skills, hosted cron
  verification, telemetry & trajectory export, and the real
  publish/binary/installer chain (via injectable runners).
- **Contract-complete with pluggable transport** — MCP `stdio` /
  HTTP/SSE (in-process `StaticMCPTransport` for tests; real process /
  socket transport is pluggable), execution environments
  (Docker/Modal/Daytona/SSH/Singularity emit deterministic dry-run
  plans that a real backend can execute), and gateway platform
  adapters (Telegram/Slack/Discord/Signal/Email adapters ship contract
  shape + fake transport; wire real HTTP at call time).

The 1035-test suite covers both tracks via injectable runners and fake
transports, so `python -m pytest -q` is fully offline and requires no
credentials.

## ProseForge Engine Boundary

Set `PROSEFORGE_ROOT` when commands need to discover or call the
canonical ProseForge engine. This repository remains the orchestration
layer and should avoid duplicating engine-owned project, pipeline, guard,
export, or report logic.

## License

MIT. See `LICENSE`.
