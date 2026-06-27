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

Every task card must contain these sections: Goal, Architecture Notes, Files, Interfaces / Contracts, TDD Steps, Verification, Acceptance, Commit Boundary. The TDD section must name the exact test, command, expected failure, implementation target, expected pass, integration check, and commit boundary.

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

## Execution Rule

Execute one card at a time. Run the card's verification commands before starting the next card. If verification fails, stop and fix the current card instead of carrying broken assumptions forward.
