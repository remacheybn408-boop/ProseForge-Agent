# System Architecture

## Layer Diagram

```text
Human / Codex / Hermes / Claude / future UI
        |
        v
pf-agent CLI / chat REPL / future TUI / local HTTP API / plugin commands
        |
        v
Agent Kernel
        |
        +--> Chat Session Manager
        +--> Intent Router
        +--> Tool Registry
        +--> Permission Policy
        +--> Event Bus
        |
        v
Workflow Engine
        |
        +--> Planning modules
        +--> Daily workbook modules
        +--> Retrieval router
        +--> Evidence pack builder
        +--> Memory store
        +--> LLM provider gateway
        +--> Report renderer
        +--> Extension registry
        |
        v
ProseForge Engine Adapter
        |
        v
$PROSEFORGE_ROOT
        |
        +--> plugin/proseforge-codex/scripts/nf_project.py
        +--> plugin/proseforge-codex/scripts/nf_pipeline.py
        +--> workspace/<slot>/novel.db
        +--> exports/
        +--> reports/
```

## Package Layout

```text
src/proseforge_agent/
|- config.py                 load and validate YAML config
|- errors.py                 typed exceptions
|- cli.py                    command entry point
|- concurrency.py            shared file lock + SQLite retry (Task 65)
|- capabilities.py           capability flags + safe-mode boot (Task 66)
|- agent/
|  |- kernel.py              per-turn agent loop
|  |- intent_router.py       chat and command intent classification
|  |- tools.py               internal tool registry
|  |- permissions.py         read/write/system permission policy
|  |- safety.py              prompt-injection guard (Task 62)
|  |- profiles.py            agent profiles and personas (Task 57)
|  `- events.py              event bus and trace records
|- chat/
|  |- session.py             chat session metadata and transcript store
|  |- repl.py                interactive terminal chat
|  |- prompts.py             chat prompt protocol (Task 36)
|  |- retrieval.py           chat retrieval and citations (Task 37)
|  |- memory.py              conversation memory extraction
|  `- handoff.py             chat-to-workflow handoff packages
|- install/
|  |- app_dirs.py            Windows/macOS/Linux config and data paths
|  |- platform_io.py         shell quoting, UTF-8, terminal caps (Task 44)
|  |- doctor.py              installation diagnostics
|  |- first_run.py           init wizard
|  |- secrets.py             native key storage adapters
|  |- provider_setup.py      provider setup wizard (Task 46)
|  |- package_checks.py      pip/pipx/source metadata checks (Task 47)
|  |- binary_packaging.py    standalone binary manifest (Task 48)
|  |- windows.py             Windows-specific doctor checks (Task 49)
|  |- macos.py               macOS-specific doctor checks (Task 50)
|  |- linux.py               Linux-specific doctor checks (Task 51)
|  |- shell.py               shell completions and launchers
|  |- migrations.py          upgrade, migration, backup (Task 53)
|  |- uninstall.py           uninstall and data retention (Task 54)
|  |- local_models.py        offline local model discovery (Task 55)
|  |- support_bundle.py      redacted operator support bundle (Task 58)
|  |- qa_matrix.py           cross-platform native QA matrix (Task 59)
|  `- ci_matrix.py           CI workflow matrix validator (Task 64)
|- adapters/
|  `- proseforge_engine.py    subprocess adapter for existing engine
|- llm/
|  |- base.py                provider protocol and result types
|  |- registry.py            role-to-provider resolution
|  |- fake.py                deterministic tests
|  |- openai_compatible.py   OpenAI-compatible APIs
|  |- anthropic_native.py    Anthropic-style native API
|  |- gemini_native.py       Gemini-style native API
|  |- usage.py               token/cost metering + budget (Task 61)
|  `- streaming.py           streaming generation channel (Task 63)
|- memory/
|  |- schema.py              Agent memory schema
|  |- store.py               SQLite access
|  |- classifier.py          memory type and tag inference
|  `- compactor.py           duplicate merge and summarization policy
|- retrieval/
|  |- query_router.py        intent to query plan
|  |- retriever.py           Agent and ProseForge source reads
|  `- evidence_pack.py       prompt-ready retrieved context
|- workflow/
|  |- models.py              run and step dataclasses
|  |- state_store.py         durable JSON state
|  |- engine.py              step runner
|  |- chapter_workflow.py    chapter lifecycle
|  `- recovery.py            retry and resume helpers
|- planning/
|  |- phase_plan.py          stage plans
|  |- daily_workbook.py      date-based daily files
|  |- market_positioning.py  market and genre strategy
|  `- templates.py           template loading
|- reports/
|  |- markdown.py            Markdown writer
|  `- json_report.py         JSON writer
|- service/
|  `- api.py                 optional local-only HTTP surface over the kernel (Task 56)
|- release/
|  `- complete_agent_gate.py release gate aggregator (Task 60)
|- extension/
|  |- contracts.py           provider, step, retriever contracts
|  `- registry.py            extension registry
`- testing/
   `- fakes.py               canonical fakes + contract harness (Task 67)
```

For the cross-cutting maintainability contract — blast-radius rules, module
ownership map, three-tier rollback, the debugging runbook, and the internal
interface compatibility policy — see `10-modularity-and-recovery.md`.

## Workspace Layout

```text
.pf-agent/ or native app data directory
|- agent.db
|- projects/
|  `- <slug>/
|     |- project_state.json
|     |- provider_state.json
|     `- bound_proseforge.json
|- phase_plans/
|  `- <slug>/
|- daily_workbooks/
|  `- <slug>/
|- evidence_packs/
|  `- <slug>/
|- workflow_runs/
|  `- <run_id>.json
|- prompts/
|  `- <slug>/
|- drafts/
|  `- <slug>/
|- reports/
|  `- <slug>/
`- logs/
```

## Data Flow For Chat Turn

```text
pf-agent chat
  -> load or create chat session
  -> classify user intent
  -> apply permission policy
  -> retrieve project or global memory when needed
  -> select provider role
  -> call model provider or internal tool
  -> render response
  -> write transcript
  -> create memory candidates
  -> emit event trace
```

## Data Flow For Chapter Run

```text
chapter run command
  -> load config
  -> load provider registry
  -> validate ProseForge root
  -> create workflow run state
  -> run nf_pipeline pre
  -> build retrieval intent
  -> query Agent memory and ProseForge sources
  -> write evidence pack
  -> build prompt pack
  -> call drafter provider or emit host prompt
  -> save draft
  -> run nf_pipeline post
  -> run nf_pipeline review
  -> write summary report
  -> extract memory changes
  -> close workflow run
```

## Dependency Direction

Allowed:

- CLI imports workflow, planning, config.
- Workflow imports adapters, retrieval, memory, llm, reports.
- Retrieval imports memory store and engine adapter read helpers.
- Provider registry imports provider implementations.

Forbidden:

- Provider implementations importing workflow.
- Memory store importing model providers.
- ProseForge engine adapter importing daily workbook logic.
- Planning modules calling providers directly.
- Chat UI calling provider implementations directly.
- Install modules importing workflow internals.

## Error Boundaries

| Boundary | Error Type | Behavior |
| --- | --- | --- |
| Config load | `ConfigurationError` | Stop command before writing artifacts |
| Engine call | `EngineAdapterError` | Mark workflow step failed and preserve stdout/stderr |
| Provider call | `ProviderError` | Save prompt pack, mark model step failed, allow retry |
| Retrieval | `RetrievalError` later, initially structured degraded result | Continue only if workflow step permits degraded retrieval |
| Memory write | `MemoryError` later, initially base error | Do not mark chapter accepted if memory update fails after accept; record follow-up |

## First Release Interfaces

### `ProseForgeEngine`

Required methods:

- `validate() -> None`
- `project_command(...) -> list[str]`
- `pipeline_command(...) -> list[str]`
- `run(cmd: list[str]) -> EngineResult`

### `LLMProvider`

Required method:

- `generate(messages: list[dict[str, str]], temperature: float = 0.7) -> GenerationResult`

### `AgentKernel`

Required method:

- `run_turn(session_id: str, user_text: str) -> AgentTurnResult`

### `ChatSessionStore`

Required methods:

- `create(mode: str, project_slug: str | None = None) -> ChatSession`
- `append_message(session_id: str, role: str, content: str) -> ChatMessage`
- `load_context(session_id: str) -> ChatContext`

### `InstallerDoctor`

Required method:

- `run() -> DoctorReport`

### `MemoryStore`

Required methods:

- `initialize()`
- `upsert_project(...) -> int`
- `add_memory(...) -> int`
- `search(...) -> list[dict]`
- `link(...) -> int`
- `record_retrieval(...) -> int`

### `WorkflowStateStore`

Required methods:

- `save(run: WorkflowRun) -> Path`
- `load(run_id: str) -> WorkflowRun`
- `append_step(run_id: str, step_result: StepResult) -> WorkflowRun`

## Hardening Interfaces (Tasks 61–65)

### `UsageMeter` / `BudgetPolicy`

- `record(provider, model, prompt_tokens, completion_tokens) -> UsageRecord`
- `check(spent) -> None` (raises `ProviderError` before a call that would exceed the budget)

### `InjectionGuard`

- `assess(content, provenance) -> SafetyVerdict` (untrusted content can only lower the permission ceiling, never raise it)

### `StreamingProvider`

- `generate_stream(messages, temperature=0.7) -> Iterator[StreamChunk]` (aggregated text equals non-streaming `generate`; non-streaming providers yield one terminal chunk)

### `FileLock` (concurrency)

- `acquire()` / `release()` plus context-manager form; `with_sqlite_retry(callable, busy_timeout)` (writers serialize; timeout raises a clean `ProseForgeAgentError`)

## Acceptance Criteria

- Every module has a single responsibility.
- Tests can instantiate each subsystem without a real LLM key.
- A failed provider call does not erase drafts or memory.
- Workflow state is written after every major step.
- ProseForge integration is isolated behind the adapter.
- Chat works without a novel project and can bind to one when requested.
- Installation and config paths are native on Windows, macOS, and Linux.
