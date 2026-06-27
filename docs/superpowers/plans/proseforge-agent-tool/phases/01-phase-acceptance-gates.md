# Phase Acceptance Gates

## Gate Format

Each phase must answer these questions:

- What can the user do now that they could not do before?
- Which files were created or changed?
- Which tests prove it?
- Which command demonstrates it?
- What failure mode is now handled?
- What remains deliberately out of scope?

## Phase 1 Gate: Package And Workspace

**User capability:** User can install/import the package and load an Agent config.

**Required files**

- `pyproject.toml`
- `configs/agent.example.yaml`
- `src/proseforge_agent/__init__.py`
- `src/proseforge_agent/errors.py`
- `src/proseforge_agent/config.py`
- `tests/test_config.py`

**Tests**

```powershell
python -m pytest tests/test_config.py -q
```

**Failure handled**

- Missing config file.
- Missing required config keys.
- Relative workspace paths.

## Phase 2 Gate: Engine Adapter

**User capability:** User can check ProseForge status through Agent code.

**Required files**

- `src/proseforge_agent/adapters/proseforge_engine.py`
- `tests/test_proseforge_adapter.py`

**Tests**

```powershell
python -m pytest tests/test_proseforge_adapter.py -q
```

**Failure handled**

- Invalid ProseForge root.
- Non-zero subprocess return code.
- Non-JSON stdout.

## Phase 3 Gate: Providers

**User capability:** User can configure model roles and run deterministic fake generation.

**Required files**

- `configs/providers.example.yaml`
- `src/proseforge_agent/llm/base.py`
- `src/proseforge_agent/llm/fake.py`
- `src/proseforge_agent/llm/registry.py`
- `src/proseforge_agent/llm/openai_compatible.py`
- `src/proseforge_agent/llm/anthropic_native.py`
- `src/proseforge_agent/llm/gemini_native.py`

**Tests**

```powershell
python -m pytest tests/test_provider_registry.py tests/test_llm_fake_and_routing.py tests/test_llm_openai_compatible.py tests/test_llm_native_adapters.py -q
```

**Failure handled**

- Missing API key.
- Unknown provider kind.
- Invalid response shape.

## Phase 4 Gate: Memory

**User capability:** User can store and search project memory.

**Required files**

- `src/proseforge_agent/memory/schema.py`
- `src/proseforge_agent/memory/store.py`
- `tests/test_memory_store.py`

**Tests**

```powershell
python -m pytest tests/test_memory_store.py -q
```

**Failure handled**

- Missing database directory.
- Empty search results.
- Usage accounting after retrieval.

## Phase 5 Gate: Retrieval

**User capability:** User can produce an evidence pack from an intent.

**Required files**

- `src/proseforge_agent/retrieval/query_router.py`
- `src/proseforge_agent/retrieval/evidence_pack.py`
- `src/proseforge_agent/retrieval/retriever.py`
- `tests/test_retrieval_router.py`

**Tests**

```powershell
python -m pytest tests/test_retrieval_router.py -q
```

**Failure handled**

- No memory found.
- Canon conflict.
- Degraded source.

## Phase 6 Gate: Plans And Daily Workbooks

**User capability:** User can generate a phase plan and a daily workbook without an LLM.

**Required files**

- `src/proseforge_agent/planning/phase_plan.py`
- `src/proseforge_agent/planning/daily_workbook.py`
- `tests/test_phase_plan.py`
- `tests/test_daily_workbook.py`

**Tests**

```powershell
python -m pytest tests/test_phase_plan.py tests/test_daily_workbook.py -q
```

**Failure handled**

- Missing date.
- Missing project title.
- Missing phase target.

## Phase 7 Gate: Workflow State

**User capability:** User can resume or inspect a workflow run.

**Required files**

- `src/proseforge_agent/workflow/models.py`
- `src/proseforge_agent/workflow/state_store.py`
- `src/proseforge_agent/workflow/recovery.py`
- `tests/test_workflow_state.py`
- `tests/test_workflow_recovery.py`

**Tests**

```powershell
python -m pytest tests/test_workflow_state.py tests/test_workflow_recovery.py -q
```

**Failure handled**

- Interrupted workflow.
- Step retry.
- Corrupt or missing state file.

## Phase 8 Gate: Chapter Lifecycle

**User capability:** User can run a chapter workflow with fake provider and adapter stubs.

**Required files**

- `src/proseforge_agent/workflow/chapter_workflow.py`
- `tests/test_chapter_workflow.py`

**Tests**

```powershell
python -m pytest tests/test_chapter_workflow.py -q
```

**Failure handled**

- `pre` failure.
- Provider failure.
- `post` failure.
- Review failure.

## Phase 9 Gate: Rewrite And Accept

**User capability:** User can run a controlled rewrite and accept sequence.

**Required files**

- `src/proseforge_agent/workflow/rewrite_workflow.py`
- `tests/test_rewrite_accept_workflow.py`

**Tests**

```powershell
python -m pytest tests/test_rewrite_accept_workflow.py -q
```

**Failure handled**

- Empty rewrite.
- Regressed guard.
- Accept failure.

## Phase 10 Gate: Release Candidate

**User capability:** User can operate the tool through CLI and read generated docs.

**Required files**

- `src/proseforge_agent/cli.py`
- `src/proseforge_agent/reports/markdown.py`
- `src/proseforge_agent/reports/json_report.py`
- `src/proseforge_agent/extension/registry.py`
- `docs/user-guide-cn.md`

**Tests**

```powershell
python -m pytest -q
```

**Failure handled**

- CLI invalid arguments.
- Report path creation.
- Extension lookup failure.
