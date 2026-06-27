# ProseForge Agent Tool Plan Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement these plans task by task. Each task card is intentionally small enough to execute, test, and review independently.

**Goal:** Build a portable `ProseForge Agent` workspace into a complete agent platform: it can chat, install cleanly on Windows/macOS/Linux, orchestrate the existing ProseForge engine, maintain deep memory, retrieve context automatically, route across many model providers, generate daily workbooks, revise chapters, and export workflows.

**Architecture:** The old single heavy plan has been split into smaller files. Start with the index, then read only the architecture or task card needed for the current work. `$PROSEFORGE_ROOT` remains the writing engine of record; the current Agent checkout becomes the agent runtime, chat, workflow, memory, model, install, native-platform, schedule, and orchestration layer.

**Tech Stack:** Python 3.10+, SQLite FTS5, YAML/JSON, pytest, argparse, existing ProseForge wrappers, OpenAI-compatible model APIs, native Anthropic/Gemini-style adapters, optional local LLM endpoints, and Markdown/JSON artifacts.

---

## How To Read This Plan

Read in this order:

1. [Split Plan Index](proseforge-agent-tool/00-index.md)
2. [Product Scope](proseforge-agent-tool/architecture/01-product-scope.md)
3. [System Architecture](proseforge-agent-tool/architecture/02-system-architecture.md)
4. [Phase Roadmap](proseforge-agent-tool/phases/00-phase-roadmap.md)
5. [Task Cards Index](proseforge-agent-tool/tasks/00-task-index.md)

Then execute one task card at a time. Do not try to implement the whole project from one file.

## Split File Map

**Architecture**

- [01 Product Scope](proseforge-agent-tool/architecture/01-product-scope.md)
- [02 System Architecture](proseforge-agent-tool/architecture/02-system-architecture.md)
- [03 ProseForge Engine Integration](proseforge-agent-tool/architecture/03-proseforge-engine-integration.md)
- [04 Deep Memory And Retrieval](proseforge-agent-tool/architecture/04-deep-memory-and-retrieval.md)
- [05 Model Provider Adapters](proseforge-agent-tool/architecture/05-model-provider-adapters.md)
- [06 Workflow Engine](proseforge-agent-tool/architecture/06-workflow-engine.md)
- [07 Extension Foundation](proseforge-agent-tool/architecture/07-extension-foundation.md)
- [08 Agent Runtime And Chat](proseforge-agent-tool/architecture/08-agent-runtime-and-chat.md)
- [09 Installation And Native Platforms](proseforge-agent-tool/architecture/09-installation-and-native-platforms.md)

**Phases And Daily Work**

- [00 Phase Roadmap](proseforge-agent-tool/phases/00-phase-roadmap.md)
- [01 Phase Acceptance Gates](proseforge-agent-tool/phases/01-phase-acceptance-gates.md)
- [01 Daily Workbook System](proseforge-agent-tool/daily/01-daily-workbook-system.md)
- [02 First 42 Days](proseforge-agent-tool/daily/02-first-42-days.md)
- [Master Calendar Index](proseforge-agent-tool/day-by-day/00-master-calendar-index.md)

**Design Principles**

- [Codex, Hermes, Claude Code Lessons](proseforge-agent-tool/design-principles/01-codex-hermes-claude-code-lessons.md)

**Provider Adaptation**

- [Provider Index](proseforge-agent-tool/providers/00-provider-index.md)
- [Provider Contract](proseforge-agent-tool/providers/01-normalized-provider-contract.md)
- [Domestic Provider Matrix](proseforge-agent-tool/providers/02-domestic-provider-matrix.md)
- [Foreign Provider Matrix](proseforge-agent-tool/providers/03-foreign-provider-matrix.md)
- [Provider Routing Policy](proseforge-agent-tool/providers/04-provider-routing-policy.md)
- [Provider Verification And Acceptance](proseforge-agent-tool/providers/05-provider-verification-and-acceptance.md)
- [Official Source Notes](proseforge-agent-tool/providers/06-official-source-notes.md)

**Task Cards**

- [00 Task Index](proseforge-agent-tool/tasks/00-task-index.md)
- Task cards live in `docs/superpowers/plans/proseforge-agent-tool/tasks/`; platform-level agent, chat, install, and native OS cards continue after Task 30.

**Appendices**

- [01 Data Contracts](proseforge-agent-tool/appendices/01-data-contracts.md)
- [02 Test Matrix](proseforge-agent-tool/appendices/02-test-matrix.md)
- [03 Risk Register](proseforge-agent-tool/appendices/03-risk-register.md)

## Current Status

This is still a planning artifact. No production code has been created yet in the Agent checkout.

Recommended next action: open [Task 01](proseforge-agent-tool/tasks/01-package-skeleton.md) and implement only that task.
