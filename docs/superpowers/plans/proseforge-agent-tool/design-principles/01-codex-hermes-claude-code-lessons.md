# Codex, Hermes, Claude Code Lessons

## Goal

ProseForge Agent should not blindly imitate one host. It should borrow the strongest ideas from Codex, Hermes, and Claude Code, then turn them into a novel-writing workflow.

## Source Notes

- OpenAI Codex docs expose durable concepts such as skills, plugins, MCP, subagents, workflows, memories, sandboxing, hooks, and multiple surfaces: <https://developers.openai.com/codex/skills>.
- OpenAI API skill docs show how reusable agent instructions can package resources and scripts: <https://developers.openai.com/api/docs/guides/tools-skills>.
- ProseForge's Hermes skill exposes a minimal tool surface: `nf_project` and `nf_pipeline`.
- Hermes Agent architecture documents a persistent agent loop, subsystem boundaries, memory, and tool execution: <https://hermes-agent.nousresearch.com/docs/developer-guide/architecture>.
- ProseForge's Claude Code skills reuse the same wrapper scripts and emphasize discipline: init before pipeline, outline before writing, pre before prose, post after prose.
- Claude Code official docs describe subagents as specialized workers with separate context, tool restrictions, permissions, hooks, memory, and automatic delegation: <https://docs.anthropic.com/en/docs/claude-code/sub-agents>.
- Claude Code skills docs separate reusable skills from operator commands: <https://code.claude.com/docs/en/skills>.

## Codex Lessons To Borrow

### 1. Durable Instructions Must Live Outside The Conversation

For ProseForge Agent:

- Project conventions belong in config and docs.
- Workflow rules belong in task cards and templates.
- Provider behavior belongs in provider profiles.
- Writing rules belong in memory.
- Daily recommendations belong in daily workbooks.

### 2. Tools Are Safer Than Vague Prompts

For ProseForge Agent:

- `nf_project` and `nf_pipeline` are engine tools.
- `provider.generate()` is the model tool.
- `MemoryStore.search()` is the memory tool.
- `EvidencePackBuilder` is the retrieval-to-prompt tool.
- `WorkflowStateStore` is the recovery tool.

### 3. Context Must Be Managed Explicitly

For ProseForge Agent:

- Do not dump all history into the model.
- Generate evidence packs.
- Keep `must_keep`, `useful_context`, and `risk_warnings` separate.
- Compact memory after accept.
- Keep raw reports outside prompts unless needed.

### 4. Multi-Surface Design Needs One Kernel

For ProseForge Agent:

- CLI, Codex, Hermes, Claude Code, and future UI must call the same Python package.
- Host-specific wrappers should be thin.
- Workflow state and artifacts must be the shared truth.

## Hermes Lessons To Borrow

### 1. Minimal Tool Surface

Hermes ProseForge exposes only two big tools:

- `nf_project`
- `nf_pipeline`

For ProseForge Agent, keep public commands similarly small:

- `pf-agent project ...`
- `pf-agent pipeline ...`
- `pf-agent daily ...`
- `pf-agent chapter ...`
- `pf-agent provider ...`
- `pf-agent memory ...`

### 2. Action Enum Instead Of Many Fragile Commands

Hermes encodes workflow through action names. For Agent:

- Use stable action names.
- Validate required arguments per action.
- Return structured results.
- Keep action schemas documented.

### 3. Engine Does Not Need To Call LLM

Existing ProseForge kernel deliberately leaves prose generation to host agents. ProseForge Agent should respect this:

- Core ProseForge remains deterministic.
- Agent layer calls LLM providers.
- Acceptance and guard reruns remain deterministic where possible.

## Claude Code Lessons To Borrow

### 1. Subagents For Context Isolation

Novel production has many noisy tasks:

- Research.
- Memory extraction.
- Continuity scan.
- Market analysis.
- Review aggregation.

Each can become a future subagent or workflow step. First release should design the boundary now:

- `research_worker`
- `memory_extractor`
- `continuity_auditor`
- `market_reader`
- `rewrite_planner`

### 2. Tool Restrictions By Role

For ProseForge Agent:

- Planner can read and write plan artifacts.
- Drafter can write drafts only.
- Rewriter can write revisions only.
- Critic can read drafts and reports, write findings.
- Memory extractor can write memory but not drafts.

### 3. Hooks And Closeout

Claude Code's hook idea maps well to novel workflows:

- Before model call: require evidence pack.
- After draft: require draft saved.
- After post: require report captured.
- After accept: require memory update.
- After daily closeout: require tomorrow recommendation.

### 4. Permission And Safety Mode

For ProseForge Agent:

- Read-only planning mode.
- Dry-run workflow mode.
- Fake-provider mode.
- Real-provider mode.
- Real-engine mutating mode.

## Resulting ProseForge Agent Design Laws

1. No writing without `pre` or equivalent context.
2. No model call without evidence pack.
3. No accepted revision without diff and guard result.
4. No hidden provider coupling.
5. No silent memory overwrite.
6. No daily work without closeout.
7. No phase completion without tests and artifacts.
8. No host-specific logic in the core workflow.
9. No provider marked certified without a request-shape test and response-parse test.
10. No long-running work without resumable state.

## Design Acceptance

These laws are accepted when every future task card states:

- Which workflow law it touches.
- Which artifact proves it.
- Which test verifies it.
