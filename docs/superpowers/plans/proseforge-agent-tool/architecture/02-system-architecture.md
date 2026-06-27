# System Architecture

## Layer Diagram

```text
Human / Codex / Hermes / Claude / future UI
        |
        v
pf-agent CLI and future plugin commands
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
|- adapters/
|  `- proseforge_engine.py    subprocess adapter for existing engine
|- llm/
|  |- base.py                provider protocol and result types
|  |- registry.py            role-to-provider resolution
|  |- fake.py                deterministic tests
|  |- openai_compatible.py   OpenAI-compatible APIs
|  |- anthropic_native.py    Anthropic-style native API
|  `- gemini_native.py       Gemini-style native API
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
`- extension/
   |- contracts.py           provider, step, retriever contracts
   `- registry.py            extension registry
```

## Workspace Layout

```text
workspace/
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

## Acceptance Criteria

- Every module has a single responsibility.
- Tests can instantiate each subsystem without a real LLM key.
- A failed provider call does not erase drafts or memory.
- Workflow state is written after every major step.
- ProseForge integration is isolated behind the adapter.
