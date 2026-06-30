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

## Complete Agent Expansion

This plan now treats ProseForge Agent as a full agent platform:

- Novel-writing workflows remain the primary professional use case.
- Chat is a first-class surface, including general chat, project chat, workflow chat, operator chat, and creative chat.
- Installation and native operation on Windows, macOS, and Linux are part of the core product, not later polish.
- Provider adaptation, memory, retrieval, permissions, and reports are shared by chat and writing workflows.

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
31. Agent runtime kernel.
32. Intent router and conversation modes.
33. Tool registry and permission policy.
34. Chat session store.
35. Chat CLI REPL.
36. Chat prompt protocol.
37. Chat retrieval and citations.
38. Chat memory and user preferences.
39. Chat-to-workflow handoff.
40. Agent event bus and background jobs.
41. First-run onboarding wizard.
42. Installation doctor.
43. Cross-platform app directories.
44. Cross-platform path, encoding, and terminal support.
45. Native secret storage.
46. Provider setup wizard.
47. pip, pipx, and source installation.
48. Standalone binary packaging.
49. Windows native support.
50. macOS native support.
51. Linux native support.
52. Shell completions and launchers.
53. Upgrade, migration, and backup.
54. Uninstall and data retention.
55. Offline local model setup.
56. Local agent service API.
57. Agent profiles and personas.
58. Operator diagnostics and support bundle.
59. Cross-platform native QA matrix.
60. Complete agent release gate.

## Cross-Cutting Hardening Cards (61–67)

These close coverage gaps in the 1–60 plan and are folded into the phase that owns each dependency (see `phases/00-phase-roadmap.md` Phase 13 and `tasks/00-task-index.md`):

61. Provider usage metering and budget.
62. Agent safety and prompt-injection guard.
63. Streaming responses.
64. Cross-platform CI pipeline.
65. Concurrency and locking.
66. Capability flags and safe-mode boot.
67. Cross-module contract and golden regression tests.

### Autonomous Agent Runtime (68–75)

These give the agent Claude-Code-class runtime maturity, with novel writing as the first vertical capability (see `architecture/11-autonomous-agent-runtime.md`):

68. Autonomous agent loop (multi-step, budgeted, context compaction).
69. Task planner and TODO tracking.
70. Self-verification and reflection/retry.
71. General tool framework (filesystem and web tools).
72. Tool execution sandbox and approval policy.
73. Sub-agent delegation.
74. Interruptibility and steering.
75. Agent eval and task-success harness.

### Product Onboarding (76)

76. Task 76: [`pf-agent setup` Guided Installation Wizard](tasks/76-pf-agent-setup-guided-install-wizard.md).

### Expansion Task Cards (77-150)

- **Setup Completion (77-80)**: [Setup Modes / 多模式 Setup 流程](tasks/77-setup-modes.md) through [First Run Bootstrap / 首次运行自动引导](tasks/80-first-run-bootstrap.md).
- **Novel Project Operations (81-87)**: [Novel Project Manifest / 小说项目总清单](tasks/81-novel-project-manifest.md) through [Publishing Metadata / 出版元数据](tasks/87-publishing-metadata.md).
- **Canon And Story Intelligence (88-94)**: [Canon Bible Manager / 显式设定 Bible](tasks/88-canon-bible-manager.md) through [Relationship Graph / 人物关系图](tasks/94-relationship-graph.md).
- **Writing Quality And Editorial Systems (95-108)**: [Writing Domain Tools Registry / 写作领域工具注册](tasks/95-writing-domain-tools-registry.md) through [Backup Verification / 备份验证](tasks/108-backup-verification.md).
- **Agent Protocol, Prompt, Context, And Audit (109-115)**: [Structured Function Calling / 结构化工具调用协议](tasks/109-structured-function-calling.md) through [Audit Trail & Debuggability / 审计追踪与调试](tasks/115-audit-trail-and-debuggability.md).
- **MCP Integration (116-122)**: [MCP Client Foundation / MCP 客户端基础](tasks/116-mcp-client-foundation.md) through [Tool Timeout / Rate Limit / Circuit Breaker](tasks/122-tool-timeout-and-rate-limit-and-circuit-breaker.md).
- **Resilience And Offline Operation (123-126)**: [Provider Fallback / Provider 降级](tasks/123-provider-fallback.md) through [Request Cache / 请求缓存与去重](tasks/126-request-cache.md).
- **Conversation Lifecycle (127-132)**: [Conversation Lifecycle / 会话生命周期管理](tasks/127-conversation-lifecycle.md) through [Multi-Context Switch / 多项目上下文切换](tasks/132-multi-context-switch.md).
- **RAG And Vector Retrieval (133-138)**: [Embeddings Abstraction / 向量嵌入抽象层](tasks/133-embeddings-abstraction.md) through [RAG Evaluation / RAG 检索评估](tasks/138-rag-evaluation.md).
- **Notifications And Jobs (139-142)**: [Notification Core / 通知核心](tasks/139-notification-core.md) through [Job Status Center / 后台任务状态中心](tasks/142-job-status-center.md).
- **Plugin Platform (143-150)**: [Plugin Manifest Spec / 插件 Manifest 规范](tasks/143-plugin-manifest-spec.md) through [Plugin Test Harness / 插件测试工具](tasks/150-plugin-test-harness.md).

### Hermes-Class Non-Desktop Expansion (151-182)

These cards target Hermes-like completeness without desktop UI shells or OS GUI automation:

- **Terminal Interface (151-154)**: [Terminal UI Foundation](tasks/151-terminal-ui-foundation.md) through [Terminal Session Operations](tasks/154-terminal-session-operations.md).
- **Messaging Gateway (155-162)**: [Messaging Gateway Core](tasks/155-messaging-gateway-core.md) through [Gateway Media And Voice Ingestion](tasks/162-gateway-media-and-voice-ingestion.md).
- **Remote Execution Environments (163-168)**: [Execution Environment Abstraction](tasks/163-execution-environment-abstraction.md) through [Process Registry And Terminal Lifecycle](tasks/168-process-registry-and-terminal-lifecycle.md).
- **Managed Tool Gateway (169-173)**: [Managed Tool Gateway Foundation](tasks/169-managed-tool-gateway-foundation.md) through [Tool Result Artifacts And Output Limits](tasks/173-tool-result-artifacts-and-output-limits.md).
- **Skill Learning Loop (174-179)**: [Skill Specification And Registry](tasks/174-skill-specification-and-registry.md) through [User Model And Memory Nudges](tasks/179-user-model-and-memory-nudges.md).
- **Hosted Ops, Observability, And Research Data (180-182)**: [Hosted Cron And Scale To Zero](tasks/180-hosted-cron-and-scale-to-zero.md) through [Middleware Hooks And Trajectory Datasets](tasks/182-middleware-hooks-and-trajectory-datasets.md).

### Release And Distribution Engineering (183-185)

Appendix track for the **actual shipping** that the packaging-readiness cards deliberately left out: Tasks 47/48 verify entry points and the binary manifest *contract*, and Task 60 aggregates the gate, but none of them run a real build or publish. Numbered at the tail so it does not renumber or reorder Cards 101–182; it depends only on the already-complete readiness work and blocks none of those cards.

- **Release And Distribution Engineering (183-185)**: [PyPI / TestPyPI Publish / 真实发布到 PyPI](tasks/183-pypi-publish.md) through [OS Installers And Signing / 安装包与签名](tasks/185-os-installers-and-signing.md).

The maintainer contract for fault isolation, three-tier rollback, the debugging runbook, and the internal interface compatibility policy lives in `architecture/10-modularity-and-recovery.md`. The autonomous runtime design lives in `architecture/11-autonomous-agent-runtime.md`.

## Definition Of Done

The project is usable when this command sequence works on a demo project:

```powershell
pf-agent init --config configs/agent.example.yaml
pf-agent doctor --config configs/agent.example.yaml
pf-agent chat --message "hello" --provider fake --no-project
pf-agent status
pf-agent phase-plan --project-title "Demo Novel" --start-date 2026-06-26 --write
pf-agent daily-workbook --date 2026-06-26 --write
pf-agent chapter run --slug demo_novel --title "Demo Novel" --vol-no 1 --chapter-no 1 --provider-role drafter
pf-agent export --slug demo_novel --format txt
pf-agent release check --complete-agent --write-report
```

The release candidate must also pass:

```powershell
python -m pytest -q
```
