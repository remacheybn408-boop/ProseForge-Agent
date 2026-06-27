# Phase 00: Plan Split And Reference Baseline

Dates: 2026-06-26 to 2026-06-28.

Goal: create a plan that is detailed enough to execute slowly without losing scope.

## Day 01: 2026-06-26, Split The Heavy Plan

Primary objective: replace the single heavy plan with a navigable plan directory.

Context to read:

- Existing ProseForge Agent request.
- Existing ProseForge plugin skill files from Codex, Hermes, and Claude-oriented packages.
- Current `docs/superpowers/plans` contents.

Work blocks:

- Morning: create the plan directory structure: `architecture`, `phases`, `daily`, `tasks`, `providers`, `design-principles`, `day-by-day`, and `appendices`.
- Midday: move the original single-plan intent into a short entry file that points to smaller documents.
- Afternoon: create task-card index and phase-roadmap index.
- Closeout: run a file list check and verify no referenced core directory is missing.

Expected outputs:

- `docs/superpowers/plans/2026-06-26-proseforge-agent-tool.md`
- `docs/superpowers/plans/proseforge-agent-tool/00-index.md`
- First generation of architecture, phase, daily, task, and appendix files.

Verification:

```powershell
Get-ChildItem -Recurse -File 'docs/superpowers/plans/proseforge-agent-tool'
```

Acceptance checklist:

- The root plan is an index, not a giant implementation document.
- Each major concern has its own folder.
- A reader can find architecture, daily planning, tasks, model providers, and risks in less than one minute.
- The original product requirements remain visible: ProseForge functions, staged plan, daily recommendation workbook, extensible foundation, deep memory, automatic retrieval, broad model support.

Stop condition:

- Stop when the split structure is readable and no core requirement disappears during the split.

Memory update:

- Record the plan-splitting rationale as project memory: large plans must be split by execution surface.

## Day 02: 2026-06-27, Extract Design Lessons

Primary objective: document what to borrow from Codex, Hermes, and Claude Code style systems.

Context to read:

- Local ProseForge Codex skill files.
- Local ProseForge Hermes skill files.
- Local ProseForge Claude-oriented skill files.
- Official Codex skill documentation when available.

Work blocks:

- Morning: write down Codex-style lessons: tool-first execution, workspace awareness, verification before completion, small task cards.
- Midday: write down Hermes-style lessons: role clarity, long-running continuity, message discipline, memory handoff.
- Afternoon: write down Claude Code-style lessons: repository-native behavior, concise operational loop, plan-to-patch discipline, explainable edits.
- Closeout: map each lesson to a concrete ProseForge Agent design decision.

Expected outputs:

- `design-principles/01-codex-hermes-claude-code-lessons.md`

Verification:

```powershell
Select-String -Path 'docs/superpowers/plans/proseforge-agent-tool/design-principles/*.md' -Pattern 'Codex','Hermes','Claude'
```

Acceptance checklist:

- The file names specific ideas, not vague inspiration.
- Every borrowed idea has a ProseForge Agent implementation consequence.
- The document distinguishes planning behavior, memory behavior, tool behavior, and review behavior.
- The design does not depend on copying any private vendor implementation.

Stop condition:

- Stop when the design-principles file can guide implementation choices during later disputes.

Memory update:

- Store the project principle: "professional fiction workflow equals agent loop plus editorial gates plus persistent memory."

## Day 03: 2026-06-28, Provider Research Baseline

Primary objective: establish the first complete provider-adaptation baseline for domestic and foreign models.

Context to read:

- Official API documentation for OpenAI, Anthropic, Google Gemini, xAI, DeepSeek, Qwen/DashScope, Zhipu GLM, Xiaomi MiMo, MiniMax, and Doubao/Volcengine.
- Existing provider adapter architecture file.

Work blocks:

- Morning: define normalized provider contract: request, response, streaming event, tool call, embedding, error, rate limit, capability metadata.
- Midday: write domestic and foreign provider matrices.
- Afternoon: write routing policy, verification policy, and certification workflow.
- Closeout: add source-note file and a docs-refresh task so unstable API details are rechecked during implementation.

Expected outputs:

- `providers/00-provider-index.md`
- `providers/01-normalized-provider-contract.md`
- `providers/02-domestic-provider-matrix.md`
- `providers/03-foreign-provider-matrix.md`
- `providers/04-provider-routing-policy.md`
- `providers/05-provider-verification-and-acceptance.md`
- `providers/06-official-source-notes.md`

Verification:

```powershell
Select-String -Path 'docs/superpowers/plans/proseforge-agent-tool/providers/*.md' -Pattern 'DeepSeek','Qwen','GLM','MiMo','MiniMax','Doubao','OpenAI','Claude','Gemini','Grok'
```

Acceptance checklist:

- Every model family explicitly requested by the user appears in the provider plan.
- Provider implementation avoids hard dependency on one vendor's API shape.
- Domestic providers and foreign providers are both first-class.
- The plan has a certification process for unstable or changing APIs.
- Base URLs and model identifiers are treated as configuration values when long-term stability is uncertain.

Stop condition:

- Stop when provider scope is complete enough that implementation can proceed without renegotiating provider categories.

Memory update:

- Record all provider families as mandatory compatibility targets.
