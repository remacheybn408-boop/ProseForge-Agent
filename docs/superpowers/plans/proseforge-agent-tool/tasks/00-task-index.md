# Task Card Index

Each card is an executable plan for one independently reviewable unit of work. The task cards are written for agentic workers and human engineers who may not know this repository.

## Environment Contract

Before executing any task, set project-local paths outside the docs:

```powershell
$env:PROSEFORGE_ROOT = "<path-to-your-ProseForge>"
$env:PROSEFORGE_AGENT_ROOT = (Get-Location).Path
```

Configuration examples must use environment variables, not machine-specific folders:

```yaml
paths:
  proseforge_root: "${PROSEFORGE_ROOT}"
  workspace_root: "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}"
```

## Required Task Card Shape

Every task card must contain these sections: Goal, Architecture Notes, Files, Interfaces / Contracts, TDD Steps, Verification, Acceptance, Commit Boundary. Platform-level cards also include Agent Product Requirement, Data Flow, Cross-Platform Notes, and Failure Modes To Prove. The TDD section must name the exact test, command, expected failure, implementation target, expected pass, integration check, and commit boundary.

## Task Order

1. [Package Skeleton](01-package-skeleton.md)
2. [Config And Workspace](02-config-and-workspace.md)
3. [ProseForge Engine Adapter](03-proseforge-engine-adapter.md)
4. [Provider Contracts And Fake Provider](04-provider-contracts-and-fake.md)
5. [OpenAI-Compatible Provider](05-openai-compatible-provider.md)
6. [Native And Local Provider Profiles](06-native-and-local-providers.md)
7. [Memory Schema And Store](07-memory-schema-and-store.md)
8. [Memory Ingestion And Compaction](08-memory-ingestion-and-compaction.md)
9. [Retrieval Router And Evidence Packs](09-retrieval-router-and-evidence-packs.md)
10. [Phase Plan Generator](10-phase-plan-generator.md)
11. [Daily Workbook Engine](11-daily-workbook-engine.md)
12. [Workflow State And Recovery](12-workflow-state-and-recovery.md)
13. [Chapter Lifecycle Workflow](13-chapter-lifecycle-workflow.md)
14. [Rewrite And Accept Workflow](14-rewrite-and-accept-workflow.md)
15. [CLI And Reports](15-cli-and-reports.md)
16. [Extension Foundation And Docs](16-extension-foundation-and-docs.md)
17. [End-To-End Demo And Release Hardening](17-e2e-demo-and-release.md)
18. [Provider Profile: OpenAI / ChatGPT](18-provider-openai-chatgpt.md)
19. [Provider Profile: Anthropic / Claude](19-provider-anthropic-claude.md)
20. [Provider Profile: Google / Gemini](20-provider-google-gemini.md)
21. [Provider Profile: xAI / Grok](21-provider-xai-grok.md)
22. [Provider Profile: DeepSeek](22-provider-deepseek.md)
23. [Provider Profile: Qwen / DashScope](23-provider-qwen-dashscope.md)
24. [Provider Profile: Zhipu GLM](24-provider-zhipu-glm.md)
25. [Provider Profile: Xiaomi MiMo](25-provider-xiaomi-mimo.md)
26. [Provider Profile: MiniMax](26-provider-minimax.md)
27. [Provider Profile: Volcengine Doubao](27-provider-volcengine-doubao.md)
28. [Provider Capability Probing](28-provider-capability-probing.md)
29. [Provider Fallback Router](29-provider-fallback-router.md)
30. [Provider Docs Refresh And Certification](30-provider-docs-refresh-and-certification.md)

31. [Agent Runtime Kernel](31-agent-runtime-kernel.md)
32. [Intent Router And Conversation Modes](32-intent-router-and-conversation-modes.md)
33. [Tool Registry And Permission Policy](33-tool-registry-and-permission-policy.md)
34. [Chat Session Store](34-chat-session-store.md)
35. [Chat CLI REPL](35-chat-cli-repl.md)
36. [Chat Prompt Protocol](36-chat-prompt-protocol.md)
37. [Chat Retrieval And Citations](37-chat-retrieval-and-citations.md)
38. [Chat Memory And User Preferences](38-chat-memory-and-user-preferences.md)
39. [Chat-To-Workflow Handoff](39-chat-to-workflow-handoff.md)
40. [Agent Event Bus And Background Jobs](40-agent-event-bus-and-background-jobs.md)
41. [First-Run Onboarding Wizard](41-first-run-onboarding-wizard.md)
42. [Installation Doctor](42-installation-doctor.md)
43. [Cross-Platform App Directories](43-cross-platform-app-directories.md)
44. [Cross-Platform Path Encoding And Terminal](44-cross-platform-path-encoding-terminal.md)
45. [Native Secret Storage](45-native-secret-storage.md)
46. [Provider Setup Wizard](46-provider-setup-wizard.md)
47. [pip, pipx, And Source Installation](47-pip-pipx-source-installation.md)
48. [Standalone Binary Packaging](48-standalone-binary-packaging.md)
49. [Windows Native Support](49-windows-native-support.md)
50. [macOS Native Support](50-macos-native-support.md)
51. [Linux Native Support](51-linux-native-support.md)
52. [Shell Completions And Launchers](52-shell-completions-and-launchers.md)
53. [Upgrade, Migration, And Backup](53-upgrade-migration-and-backup.md)
54. [Uninstall And Data Retention](54-uninstall-and-data-retention.md)
55. [Offline Local Model Setup](55-offline-local-model-setup.md)
56. [Local Agent Service API](56-local-agent-service-api.md)
57. [Agent Profiles And Personas](57-agent-profiles-and-personas.md)
58. [Operator Diagnostics And Support Bundle](58-operator-diagnostics-and-support-bundle.md)
59. [Cross-Platform Native QA Matrix](59-cross-platform-native-qa-matrix.md)
60. [Complete Agent Release Gate](60-complete-agent-release-gate.md)

## Hardening Cards (61–65)

These cards close coverage gaps in the 1–60 plan. They are numbered as an appendix to avoid renumbering existing cards; each notes the point in the 1–60 order after which it should logically execute.

61. [Provider Usage Metering And Budget](61-provider-usage-metering-and-budget.md) — execute after Tasks 04–06 (provider layer).
62. [Agent Safety And Prompt-Injection Guard](62-agent-safety-and-prompt-injection-guard.md) — execute after Task 33 (permissions) and Task 09 (retrieval).
63. [Streaming Responses](63-streaming-responses.md) — execute after Tasks 04–06 and Task 35 (chat REPL).
64. [Cross-Platform CI Pipeline](64-cross-platform-ci-pipeline.md) — execute after Task 01; strengthen as Tasks 49–51, 59 land.
65. [Concurrency And Locking](65-concurrency-and-locking.md) — execute after Task 07 (memory), Task 12 (workflow state), and Task 40 (jobs).
66. [Capability Flags And Safe-Mode Boot](66-capability-flags-and-safe-mode.md) — execute after Task 42 (doctor) and Task 40 (events).
67. [Cross-Module Contract And Golden Regression Tests](67-contract-and-golden-tests.md) — establish canonical fakes after Task 04; add boundary/golden cases as subsystems land; consumed by Tasks 64 and 60.

## Autonomous Agent Runtime Cards (68–75)

These give the agent Claude-Code-class runtime maturity with novel writing as the first vertical capability. See [Autonomous Agent Runtime](../architecture/11-autonomous-agent-runtime.md).

68. [Autonomous Agent Loop](68-autonomous-agent-loop.md) — execute after Task 31 (kernel).
69. [Task Planner And TODO Tracking](69-task-planner-and-todo.md) — execute after Task 31; consumed by Task 68.
70. [Self-Verification And Reflection](70-self-verification-and-reflection.md) — execute after Tasks 31 and 69; ProseForge gates register as domain verifiers.
71. [General Tool Framework And Filesystem/Web Tools](71-general-tool-framework.md) — execute after Task 33; reuses Task 02 path containment and Task 62 safety.
72. [Tool Execution Sandbox And Approval Policy](72-tool-execution-sandbox.md) — execute after Tasks 33, 62, and 71.
73. [Sub-Agent Delegation](73-sub-agent-delegation.md) — execute after Tasks 68, 69, and 33.
74. [Interruptibility And Steering](74-interruptibility-and-steering.md) — execute after Tasks 68 and 69.
75. [Agent Eval And Task-Success Harness](75-agent-eval-harness.md) — execute after Tasks 68 and 70; consumed by Tasks 64 and 60.

The maintainability contract these cards enforce is documented in [Modularity, Fault Isolation, And Recovery](../architecture/10-modularity-and-recovery.md). The autonomous runtime design is in [Autonomous Agent Runtime](../architecture/11-autonomous-agent-runtime.md).

## Product Onboarding Cards (76)

76. [pf-agent setup Guided Installation Wizard](76-pf-agent-setup-guided-install-wizard.md) — execute after Tasks 41–55 and before relying on product-grade first use.

## Execution Rule

Execute one card at a time. Run the card's verification commands before starting the next card. If verification fails, stop and fix the current card instead of carrying broken assumptions forward.
