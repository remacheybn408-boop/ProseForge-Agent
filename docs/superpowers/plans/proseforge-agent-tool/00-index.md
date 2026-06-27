# ProseForge Agent Split Plan

This directory replaces the original single heavy plan. It is designed for incremental execution: one subsystem, one task card, one verification pass.

## Project Intent

`ProseForge Agent` turns novel writing into an agentic production workflow:

- It keeps the existing ProseForge engine as the source of truth for project slots, pipeline actions, guards, reports, and exports.
- It adds an orchestration layer that can plan, retrieve, draft, review, revise, remember, and recommend the next day's work.
- It treats long-form fiction as an engineering system: every chapter has inputs, constraints, retrieved evidence, output artifacts, review gates, and memory updates.

## What Was Wrong With The Single File

The original plan was too heavy because it mixed five different jobs:

- Product definition.
- Architecture design.
- Phase roadmap.
- Daily writing calendar.
- Implementation task cards.

Those jobs now live in separate files. Each file has one responsibility and can be updated without forcing the reader to load the whole project.

## Directory Roles

```text
architecture/  product and system design
phases/        stage-by-stage project delivery plan
daily/         date-based writing and engineering workbooks
day-by-day/    exact daily execution calendar per phase
design-principles/ Codex, Hermes, Claude Code design lessons
providers/     full model-provider adaptation plan
tasks/         small implementation cards with tests and acceptance criteria
appendices/    contracts, test matrix, risk register
```

## Execution Rule

Do not execute more than one task card without running its verification command and updating the task status. The project is large enough that partial, unverified progress will become confusing quickly.

## Required Implementation Sequence

1. Package skeleton.
2. Configuration and workspace.
3. ProseForge engine adapter.
4. Provider contracts and fake model.
5. OpenAI-compatible provider.
6. Native and local provider profiles.
7. Memory schema and store.
8. Memory ingestion, classification, and compaction.
9. Retrieval router and evidence packs.
10. Phase planning generator.
11. Daily workbook engine.
12. Workflow state and recovery.
13. Chapter lifecycle.
14. Rewrite and accept loop.
15. CLI and report rendering.
16. Extension foundation.
17. End-to-end demo and release hardening.
18. Provider profile: OpenAI / ChatGPT.
19. Provider profile: Anthropic / Claude.
20. Provider profile: Google / Gemini.
21. Provider profile: xAI / Grok.
22. Provider profile: DeepSeek.
23. Provider profile: Alibaba Qwen / DashScope.
24. Provider profile: Zhipu GLM.
25. Provider profile: Xiaomi MiMo.
26. Provider profile: MiniMax.
27. Provider profile: Volcengine Doubao.
28. Provider capability probing.
29. Provider fallback router.
30. Provider docs refresh and certification.

## Definition Of Done

The project is usable when this command sequence works on a demo project:

```powershell
pf-agent init --config configs/agent.example.yaml
pf-agent status
pf-agent phase-plan --project-title "Demo Novel" --start-date 2026-06-26 --write
pf-agent daily-workbook --date 2026-06-26 --write
pf-agent chapter run --slug demo_novel --title "Demo Novel" --vol-no 1 --chapter-no 1 --provider-role drafter
pf-agent export --slug demo_novel --format txt
```

The release candidate must also pass:

```powershell
python -m pytest -q
```
