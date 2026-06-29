# Phase Roadmap

## Roadmap Principle

Each phase must produce working, testable software. A phase is not complete because files exist; it is complete only when its verification commands pass and its artifacts can be inspected.

## Phase 0: Planning Split And Project Shape

**Purpose:** Replace the single heavy plan with a split planning system that can be executed incrementally.

**Inputs**

- User requirement: ProseForge should become an agent tool.
- Existing ProseForge repo: `$PROSEFORGE_ROOT`.
- Agent workspace: `$PROSEFORGE_AGENT_ROOT`.

**Outputs**

- Lightweight entry index.
- Architecture files.
- Phase files.
- Daily files.
- Task cards.
- Appendices.

**Done When**

- Each requirement maps to at least one file and at least one task card.
- No single planning file is too heavy to read.
- Task cards can be executed one at a time.

## Phase 1: Package And Workspace Foundation

**Purpose:** Create a minimal Python package with deterministic tests and configuration loading.

**Outputs**

- `pyproject.toml`
- `src/proseforge_agent/__init__.py`
- `src/proseforge_agent/errors.py`
- `src/proseforge_agent/config.py`
- `configs/agent.example.yaml`
- `tests/test_config.py`

**Core Decisions**

- Use Python 3.10+.
- Use `pyyaml` for config.
- Keep config explicit.
- Do not auto-discover random parent directories for the Agent workspace.

**Verification**

```powershell
python -m pytest tests/test_config.py -q
```

## Phase 2: ProseForge Engine Integration

**Purpose:** Expose ProseForge project and pipeline actions through a safe adapter.

**Outputs**

- `src/proseforge_agent/adapters/proseforge_engine.py`
- `tests/test_proseforge_adapter.py`
- Safe smoke command docs.

**Core Decisions**

- First version uses subprocess calls.
- Always pass `--project-root`.
- Capture stdout/stderr.
- Parse JSON when possible but keep raw output.

**Verification**

```powershell
python -m pytest tests/test_proseforge_adapter.py -q
pf-agent proseforge inspect --root "${PROSEFORGE_ROOT}" --dry-run
```

## Phase 3: Model Provider Layer

**Purpose:** Allow workflows to call model roles instead of hard-coded providers.

**Outputs**

- Provider protocol.
- Fake provider.
- Provider registry.
- OpenAI-compatible adapter.
- Anthropic native adapter.
- Gemini native adapter.
- Provider example config.

**Core Decisions**

- Tests must run without network.
- Domestic and local providers are configured through `openai_compatible`.
- Native adapters are used only where request/response shape differs.

**Verification**

```powershell
python -m pytest tests/test_provider_registry.py tests/test_llm_fake_and_routing.py -q
python -m pytest tests/test_llm_openai_compatible.py tests/test_llm_native_adapters.py -q
```

## Phase 4: Deep Memory

**Purpose:** Create Agent-owned memory that survives across workflow runs and can be searched.

**Outputs**

- `workspace/agent.db`
- `memory_items`
- `memory_links`
- `retrieval_logs`
- FTS5 index.
- Memory store tests.

**Core Decisions**

- Keep Agent memory separate from ProseForge `novel.db`.
- Link to ProseForge through source references.
- Store importance and confidence.
- Track use count.

**Verification**

```powershell
python -m pytest tests/test_memory_store.py -q
```

## Phase 5: Automatic Retrieval

**Purpose:** Build evidence packs automatically before model calls.

**Outputs**

- Retrieval intent type.
- Query router.
- Evidence pack builder.
- Retrieval log persistence.
- Degraded retrieval behavior.

**Core Decisions**

- The first version starts with Agent memory FTS5.
- ProseForge DB retrieval is added behind source-specific methods.
- Canon facts and reader promises go to `must_keep`.

**Verification**

```powershell
python -m pytest tests/test_retrieval_router.py -q
```

## Phase 6: Planning And Daily Workbooks

**Purpose:** Generate phase plans and date-based daily workbooks.

**Outputs**

- Phase plan generator.
- Daily workbook generator.
- Calendar recommendation logic.
- Markdown writer.

**Core Decisions**

- Daily workbook must include exact date.
- Daily workbook must include retrieval plan.
- Daily workbook must include closeout checklist.
- It must work without LLM calls.

**Verification**

```powershell
python -m pytest tests/test_phase_plan.py tests/test_daily_workbook.py -q
```

## Phase 7: Workflow State And Recovery

**Purpose:** Make workflows resumable and inspectable.

**Outputs**

- Workflow run dataclass.
- Step result dataclass.
- State store.
- Recovery helpers.

**Core Decisions**

- Save state after every major step.
- Save prompt before provider call.
- Save evidence before prompt.
- Failed steps can be retried.

**Verification**

```powershell
python -m pytest tests/test_workflow_state.py tests/test_workflow_recovery.py -q
```

## Phase 8: Chapter Lifecycle

**Purpose:** Orchestrate `pre -> retrieve -> draft -> save -> post -> review`.

**Outputs**

- Chapter workflow.
- Draft artifact writer.
- Prompt pack writer.
- ProseForge command recording.

**Core Decisions**

- First release can use fake provider to prove flow.
- Drafts are versioned.
- ProseForge post/review are authoritative quality checks.

**Verification**

```powershell
python -m pytest tests/test_chapter_workflow.py -q
```

## Phase 9: Rewrite And Accept Loop

**Purpose:** Connect ProseForge rewrite cards to provider-based rewriting and `accept`.

**Outputs**

- Rewrite workflow.
- Revised draft writer.
- Accept command integration.
- Diff report capture.

**Core Decisions**

- Never overwrite original draft.
- Accept appends or delegates to ProseForge versioning.
- Regressed guards block automatic closeout.

**Verification**

```powershell
python -m pytest tests/test_rewrite_accept_workflow.py -q
```

## Phase 10: CLI, Reports, Extensions, Release

**Purpose:** Make the writing workflow usable from command line and ready for future plugin surfaces.

**Outputs**

- CLI commands.
- Markdown report renderer.
- JSON report renderer.
- Extension registry.
- User guide.
- End-to-end demo.

**Verification**

```powershell
python -m pytest -q
pf-agent phase-plan --project-title "Demo Novel" --start-date 2026-06-26
pf-agent daily-workbook --date 2026-06-26 --project-title "Demo Novel" --phase-name "Foundation" --main-target "Create package skeleton"
```

## Phase 11: Agent Runtime And Chat

**Purpose:** Turn the tool into a complete conversational agent, not only a novel workflow runner.

**Outputs**

- Agent Kernel.
- Intent router.
- Conversation modes.
- Tool registry and permissions.
- Chat session store.
- Chat CLI REPL.
- Chat retrieval and citations.
- Chat memory candidates.
- Chat-to-workflow handoff.
- Agent event bus.

**Core Decisions**

- Chat works without a novel project.
- Project chat can bind to a project and cite memory, reports, plans, and workflow state.
- Chat cannot mutate project, engine, secrets, or shell integration without permission.
- Chat creates memory candidates, not automatically accepted canon.
- The same kernel must support CLI chat, future TUI, future desktop UI, and local API.

**Verification**

```powershell
python -m pytest tests/test_agent_kernel.py tests/test_intent_router.py tests/test_chat_cli_repl.py -q
pf-agent chat --message "hello" --provider fake --no-project
pf-agent chat drill --all-modes --provider fake --write-report
```

## Phase 12: Installation And Native Platforms

**Purpose:** Make ProseForge Agent installable and native on Windows, macOS, and Linux.

**Outputs**

- First-run onboarding wizard.
- Installation doctor.
- Native app directory resolver.
- Path, encoding, and terminal utilities.
- Native secret storage adapters.
- Provider setup wizard.
- Source, pip, pipx, and standalone packaging checks.
- Windows native support.
- macOS native support.
- Linux native support.
- Shell completions and launchers.
- Upgrade, migration, backup, uninstall, local model setup, local API, personas, support bundle, and native QA matrix.

**Core Decisions**

- No install or config document may contain machine-specific absolute paths.
- `pf-agent init`, `pf-agent doctor`, and `pf-agent chat --message` must work on all three operating systems.
- Native secret storage is preferred; environment variables remain a visible fallback.
- Packaging is verified before release, not treated as documentation only.

**Verification**

```powershell
python -m pytest tests/test_first_run_onboarding.py tests/test_installation_doctor.py tests/test_app_dirs.py -q
python -m pytest tests/test_windows_native_support.py tests/test_macos_native_support.py tests/test_linux_native_support.py -q
pf-agent release check --complete-agent --write-report
```

## Phase 13: Hardening (Cross-Cutting)

**Purpose:** Close coverage gaps that span the earlier phases — spend control, agent safety, streaming UX, continuous cross-platform verification, and concurrency. These are the Hardening Cards (61–65); each is folded into the phase that owns its dependency rather than run as a strict trailing block.

**Outputs**

- Provider usage metering and budget (Task 61) — folds into Phase 3.
- Agent safety and prompt-injection guard (Task 62) — folds into Phase 11.
- Streaming responses (Task 63) — folds into Phases 3 and 11.
- Cross-platform CI pipeline (Task 64) — established after Phase 1, strengthened through Phase 12.
- Concurrency and locking (Task 65) — folds into Phases 4, 7, and 11.

**Core Decisions**

- Budgets stop spend before a call and preserve the prompt pack for resume.
- Untrusted content can never raise the permission ceiling.
- Streaming output must aggregate to the same text as non-streaming.
- CI runs the suite on Windows, macOS, and Linux on every change.
- Shared state writes serialize through one cross-platform lock.

**Verification**

```powershell
python -m pytest tests/test_provider_usage_metering.py tests/test_agent_safety_guard.py tests/test_streaming_responses.py -q
python -m pytest tests/test_ci_pipeline.py tests/test_concurrency_locking.py -q
```

## Phase 14: Autonomous Agent Runtime

**Purpose:** Give the agent Claude-Code-class runtime maturity — a bounded multi-step autonomous loop, task decomposition, self-verification, a general tool framework with a sandbox, sub-agent delegation, interruptibility, and a task-success eval harness. Novel writing becomes the first vertical capability on this runtime (see `architecture/11-autonomous-agent-runtime.md`).

**Outputs**

- Autonomous agent loop with budgets and context compaction (Task 68).
- Task planner and TODO tracking (Task 69).
- Self-verification and reflection/retry; ProseForge gates as domain verifiers (Task 70).
- General tool framework: filesystem and web tools (Task 71).
- Tool execution sandbox and approval policy (Task 72).
- Sub-agent delegation (Task 73).
- Interruptibility and steering (Task 74).
- Agent eval and task-success harness (Task 75).

**Core Decisions**

- The loop reuses the per-turn kernel (Task 31) unmodified.
- Every run is bounded by iteration and cost budgets, a no-progress detector, and interruptibility.
- Write/execute tools are gated by permission, safety, sandbox, and approval.
- Task-success rate is an enforced release gate.

**Verification**

```powershell
python -m pytest tests/test_agent_loop.py tests/test_task_planner.py tests/test_self_verification.py -q
python -m pytest tests/test_general_tools.py tests/test_tool_sandbox.py tests/test_sub_agent.py tests/test_control_interrupt.py -q
python -m pytest tests/eval -q
pf-agent run --goal "draft a one-line opening" --provider fake --max-iterations 5
```

## Phase 15: Product Onboarding Polish

**Purpose:** Turn the install pieces into one guided first-use path through Task 76.

**Outputs**

- `pf-agent setup` guided installation wizard.
- Minimal, quick, full, non-interactive, reconfigure, add-provider, repair, and print-config modes.
- First-run bootstrap guidance for uninitialized chat, daily workbook, chapter, and provider commands.

**Core Decisions**

- Setup assembles existing install modules instead of rewriting them.
- Fake provider remains the no-key fallback.
- Provider, shell, keyring, network, and engine failures become warnings unless they make the local filesystem setup impossible.
- Raw API keys are never written to config or summary output.

**Verification**

```powershell
python -m pytest tests/setup -q
pf-agent setup --minimal
pf-agent doctor
pf-agent chat --provider fake --message "hello"
pf-agent setup --print-config
```
