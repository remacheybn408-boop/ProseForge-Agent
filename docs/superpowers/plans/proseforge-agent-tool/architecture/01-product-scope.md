# Product Scope

## One-Sentence Definition

`ProseForge Agent` is a professional long-form novel production agent that wraps ProseForge into a daily workflow for planning, drafting, revision, memory, retrieval, model routing, quality gates, and export.

## User Requirements

The user explicitly required six things:

1. Implement ProseForge functionality.
2. Produce a plan for every stage.
3. Produce date-based daily recommended workbooks.
4. Build a foundation that is easy to extend later.
5. Provide deep memory and automatic retrieval.
6. Support common domestic, foreign, and local large model providers.

## Product Principles

### 1. The Author Must Never Write Blind

Before a model or human writes a chapter, the system must retrieve:

- The current chapter plan.
- Recent chapter summaries.
- Character states.
- Open reader promises.
- Active plot threads.
- Relevant world rules.
- Writing rules learned from review.
- Guard and editor warnings from previous chapters.

### 2. ProseForge Engine Remains The Canonical Writing Engine

`$PROSEFORGE_ROOT` already owns:

- Project and slot management.
- `pre`, `post`, `review`, `rewrite`, `accept`, `volume`, `export`.
- Novel SQLite databases.
- Guards and review reports.

The Agent must integrate these functions instead of reimplementing them.

### 3. The Agent Owns Orchestration

`$PROSEFORGE_AGENT_ROOT` owns:

- Model calls.
- Provider routing.
- Daily schedule.
- Evidence packs.
- Agent memory.
- Workflow state and recovery.
- Human-facing plans and workbooks.
- Extension registry.

### 4. Every Output Is An Artifact

The system writes durable artifacts:

- Phase plans.
- Daily workbooks.
- Evidence packs.
- Prompt packs.
- Draft versions.
- Review summaries.
- Retrieval logs.
- Memory changes.
- Workflow run states.

### 5. Extension Is A First-Class Requirement

No core workflow should depend directly on one provider, one storage backend, one UI, or one host agent. Later additions should fit by registering:

- A provider.
- A workflow step.
- A retriever.
- A report renderer.
- A memory classifier.
- A template.

## In Scope

- Python package in `$PROSEFORGE_AGENT_ROOT`.
- Config files for Agent and providers.
- CLI named `pf-agent`.
- Subprocess adapter for existing ProseForge wrappers.
- Deep memory database.
- FTS5 retrieval for Agent memory.
- Optional integration with ProseForge's own FTS/RAG.
- Provider abstraction and fake provider for tests.
- OpenAI-compatible provider.
- Native Anthropic-style and Gemini-style provider adapters.
- Local OpenAI-compatible model endpoint support.
- Phase plan generation.
- Daily workbook generation.
- Chapter lifecycle orchestration.
- Rewrite and accept orchestration.
- Markdown and JSON reports.
- Test suite.

## Out Of Scope For First Release

- Full web UI.
- Paid billing.
- Multi-user collaboration.
- Cloud sync.
- Vector database as a required dependency.
- Automatic publication to platforms.
- Fine-tuning.
- Real-time collaborative editing.

These are intentionally deferred because the first release needs a strong foundation.

## Primary User Flows

### Flow A: First Project Setup

1. User creates or opens `$PROSEFORGE_AGENT_ROOT`.
2. User configures `configs/agent.yaml`.
3. Agent validates `$PROSEFORGE_ROOT`.
4. Agent initializes `workspace/agent.db`.
5. Agent binds to a ProseForge slot.
6. Agent generates a phase plan.

### Flow B: Daily Writing

1. User runs daily workbook.
2. Agent reads current workflow state.
3. Agent recommends the next chapter or planning task.
4. Agent retrieves memory and ProseForge evidence.
5. Agent writes a workbook file for the date.
6. User or model completes the target.
7. Agent records closeout and tomorrow recommendation.

### Flow C: Chapter Production

1. Agent runs ProseForge `pre`.
2. Agent builds retrieval intent.
3. Agent builds evidence pack.
4. Agent calls drafter provider or prepares prompt for host model.
5. Agent saves draft.
6. Agent runs ProseForge `post`.
7. Agent runs `review`.
8. Agent generates rewrite card.
9. Agent calls rewriter provider.
10. Agent runs `accept`.
11. Agent updates memory.

## Acceptance Criteria

- User can see exactly where each artifact is written.
- User can resume from a failed workflow run.
- User can swap model providers by config.
- User can inspect what evidence was retrieved before writing.
- User can run daily recommendations without invoking an LLM.
- User can use fake providers to test the workflow without API keys.
