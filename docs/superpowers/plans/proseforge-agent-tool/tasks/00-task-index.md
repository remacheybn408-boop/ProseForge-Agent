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

## Expansion Task Cards (77-150)

### Setup Completion Cards (77-80)

77. [Setup Modes / 多模式 Setup 流程](77-setup-modes.md)
78. [Setup Config Generator / 智能配置生成器](78-setup-config-generator.md)
79. [Setup Recovery / 重新配置与修复](79-setup-recovery.md)
80. [First Run Bootstrap / 首次运行自动引导](80-first-run-bootstrap.md)

### Novel Project Operations Cards (81-87)

81. [Novel Project Manifest / 小说项目总清单](81-novel-project-manifest.md)
82. [Artifact Graph / 稿件产物依赖图](82-artifact-graph.md)
83. [Bulk Import / 批量导入已有稿件](83-bulk-import.md)
84. [Scene-Level Workflow / 场景级写作流程](84-scene-level-workflow.md)
85. [Chapter Reorganization / 章节重排](85-chapter-reorganization.md)
86. [Export / Compilation Pipeline / 小说导出与编译](86-export-and-compilation-pipeline.md)
87. [Publishing Metadata / 出版元数据](87-publishing-metadata.md)

### Canon And Story Intelligence Cards (88-94)

88. [Canon Bible Manager / 显式设定 Bible](88-canon-bible-manager.md)
89. [Continuity Conflict Resolver / 设定冲突仲裁](89-continuity-conflict-resolver.md)
90. [Timeline Engine / 时间线引擎](90-timeline-engine.md)
91. [Plot Thread Manager / 情节线管理器](91-plot-thread-manager.md)
92. [Foreshadowing Tracker / 伏笔追踪器](92-foreshadowing-tracker.md)
93. [Character Arc Tracker / 人物弧光追踪](93-character-arc-tracker.md)
94. [Relationship Graph / 人物关系图](94-relationship-graph.md)

### Writing Quality And Editorial Systems Cards (95-108)

95. [Writing Domain Tools Registry / 写作领域工具注册](95-writing-domain-tools-registry.md)
96. [Explicit Writing Rules / 显式写作规则管理](96-explicit-writing-rules.md)
97. [Tone / Style Profile Compiler / 风格规则编译器](97-tone-and-style-profile-compiler.md)
98. [Writing Quality Gates / 写作质量门](98-writing-quality-gates.md)
99. [Literary Regression Suite / 文风回归测试](99-literary-regression-suite.md)
100. [Rewrite Strategy Library / 改稿策略库](100-rewrite-strategy-library.md)
101. [Reader Experience Review / 读者体验审稿](101-reader-experience-review.md)
102. [Manuscript Search / 全书稿件搜索](102-manuscript-search.md)
103. [Project Health Doctor / 小说项目健康检查](103-project-health-doctor.md)
104. [Draft Versioning / Diff / Branch / 稿件版本管理](104-draft-versioning-and-diff-and-branch.md)
105. [Editorial Pipeline / 编辑工序流水线](105-editorial-pipeline.md)
106. [Human Approval Queue / 人类审批队列](106-human-approval-queue.md)
107. [Writing Analytics / 写作统计分析](107-writing-analytics.md)
108. [Backup Verification / 备份验证](108-backup-verification.md)

### Agent Protocol, Prompt, Context, And Audit Cards (109-115)

109. [Structured Function Calling / 结构化工具调用协议](109-structured-function-calling.md)
110. [Structured Output Repair / 结构化输出修复](110-structured-output-repair.md)
111. [Context Window Management / 上下文窗口管理](111-context-window-management.md)
112. [System Prompt Management / 系统提示管理](112-system-prompt-management.md)
113. [Prompt Template Registry / Prompt 模板注册表](113-prompt-template-registry.md)
114. [Multimodal / Attachment Ingestion / 多模态与附件输入](114-multimodal-and-attachment-ingestion.md)
115. [Audit Trail & Debuggability / 审计追踪与调试](115-audit-trail-and-debuggability.md)

### MCP Integration Cards (116-122)

116. [MCP Client Foundation / MCP 客户端基础](116-mcp-client-foundation.md)
117. [MCP Server Registry / MCP Server 注册表](117-mcp-server-registry.md)
118. [MCP Security Boundary / MCP 安全边界](118-mcp-security-boundary.md)
119. [MCP Tool Approval Gate / MCP 工具审批门](119-mcp-tool-approval-gate.md)
120. [MCP Tool Schema Validation / MCP 工具 Schema 校验](120-mcp-tool-schema-validation.md)
121. [MCP Credentials Boundary / MCP 凭证隔离](121-mcp-credentials-boundary.md)
122. [Tool Timeout / Rate Limit / Circuit Breaker](122-tool-timeout-and-rate-limit-and-circuit-breaker.md)

### Resilience And Offline Operation Cards (123-126)

123. [Provider Fallback / Provider 降级](123-provider-fallback.md)
124. [Graceful Degradation / 功能分级降级](124-graceful-degradation.md)
125. [Offline Mode / 离线模式](125-offline-mode.md)
126. [Request Cache / 请求缓存与去重](126-request-cache.md)

### Conversation Lifecycle Cards (127-132)

127. [Conversation Lifecycle / 会话生命周期管理](127-conversation-lifecycle.md)
128. [Cross-session Search / 跨会话搜索](128-cross-session-search.md)
129. [Session Export / Import / 会话导入导出](129-session-export-and-import.md)
130. [Session Branching / 会话分支](130-session-branching.md)
131. [Session Merge / 会话合并](131-session-merge.md)
132. [Multi-Context Switch / 多项目上下文切换](132-multi-context-switch.md)

### RAG And Vector Retrieval Cards (133-138)

133. [Embeddings Abstraction / 向量嵌入抽象层](133-embeddings-abstraction.md)
134. [Vector Store Adapters / 向量库适配器](134-vector-store-adapters.md)
135. [Hybrid Retrieval / 混合检索](135-hybrid-retrieval.md)
136. [RAG Ingestion Pipeline / RAG 入库流水线](136-rag-ingestion-pipeline.md)
137. [Evidence Pack Retrieval / Evidence Pack 检索融合](137-evidence-pack-retrieval.md)
138. [RAG Evaluation / RAG 检索评估](138-rag-evaluation.md)

### Notifications And Jobs Cards (139-142)

139. [Notification Core / 通知核心](139-notification-core.md)
140. [Desktop Notifications / 桌面原生通知](140-desktop-notifications.md)
141. [Webhook Notifications / Webhook 推送](141-webhook-notifications.md)
142. [Job Status Center / 后台任务状态中心](142-job-status-center.md)

### Plugin Platform Cards (143-150)

143. [Plugin Manifest Spec / 插件 Manifest 规范](143-plugin-manifest-spec.md)
144. [Plugin Discovery / 插件发现](144-plugin-discovery.md)
145. [Plugin Install / Update / Remove CLI](145-plugin-install-update-and-remove-cli.md)
146. [Plugin Permission Model / 插件权限模型](146-plugin-permission-model.md)
147. [Plugin Sandbox / 插件沙箱](147-plugin-sandbox.md)
148. [Plugin Dependency Management / 插件依赖管理](148-plugin-dependency-management.md)
149. [Plugin Hooks / 插件生命周期钩子](149-plugin-hooks.md)
150. [Plugin Test Harness / 插件测试工具](150-plugin-test-harness.md)

## Hermes-Class Non-Desktop Expansion Cards (151-182)

These cards close the gap between the current ProseForge Agent platform plan and Hermes-class non-desktop operation: terminal/TUI maturity, remote messaging, remote execution environments, managed tools, skill learning, hosted jobs, observability, middleware, and trajectory data. They explicitly exclude desktop UI shells and OS GUI automation.

### Terminal Interface Cards (151-154)

151. [Terminal UI Foundation](151-terminal-ui-foundation.md)
152. [Slash Command Registry](152-slash-command-registry.md)
153. [Streaming Tool Output](153-streaming-tool-output.md)
154. [Terminal Session Operations](154-terminal-session-operations.md)

### Messaging Gateway Cards (155-162)

155. [Messaging Gateway Core](155-messaging-gateway-core.md)
156. [Platform Adapter Contract](156-platform-adapter-contract.md)
157. [Telegram Gateway Adapter](157-telegram-gateway-adapter.md)
158. [Discord And Slack Gateway Adapters](158-discord-and-slack-gateway-adapters.md)
159. [WhatsApp Signal Email Gateway Adapters](159-whatsapp-signal-email-gateway-adapters.md)
160. [Gateway Relay Auth And Pairing](160-gateway-relay-auth-and-pairing.md)
161. [Gateway Delivery Reliability](161-gateway-delivery-reliability.md)
162. [Gateway Media And Voice Ingestion](162-gateway-media-and-voice-ingestion.md)

### Remote Execution Environment Cards (163-168)

163. [Execution Environment Abstraction](163-execution-environment-abstraction.md)
164. [Local And Docker Execution Backends](164-local-and-docker-execution-backends.md)
165. [SSH And Singularity Execution Backends](165-ssh-and-singularity-execution-backends.md)
166. [Modal And Daytona Execution Backends](166-modal-and-daytona-execution-backends.md)
167. [Remote File Sync And Checkpoints](167-remote-file-sync-and-checkpoints.md)
168. [Process Registry And Terminal Lifecycle](168-process-registry-and-terminal-lifecycle.md)

### Managed Tool Gateway Cards (169-173)

169. [Managed Tool Gateway Foundation](169-managed-tool-gateway-foundation.md)
170. [Web Search And URL Safety Tools](170-web-search-and-url-safety-tools.md)
171. [Cloud Browser Tool Adapter](171-cloud-browser-tool-adapter.md)
172. [Media Generation And Transcription Tools](172-media-generation-and-transcription-tools.md)
173. [Tool Result Artifacts And Output Limits](173-tool-result-artifacts-and-output-limits.md)

### Skill Learning Loop Cards (174-179)

174. [Skill Specification And Registry](174-skill-specification-and-registry.md)
175. [Skill Hub Install And Sync](175-skill-hub-install-and-sync.md)
176. [Autonomous Skill Creation](176-autonomous-skill-creation.md)
177. [Skill Self Improvement And Provenance](177-skill-self-improvement-and-provenance.md)
178. [Skill Usage Analytics And Safety Audit](178-skill-usage-analytics-and-safety-audit.md)
179. [User Model And Memory Nudges](179-user-model-and-memory-nudges.md)

### Hosted Ops, Observability, And Research Data Cards (180-182)

180. [Hosted Cron And Scale To Zero](180-hosted-cron-and-scale-to-zero.md)
181. [Observer Hooks And Telemetry Export](181-observer-hooks-and-telemetry-export.md)
182. [Middleware Hooks And Trajectory Datasets](182-middleware-hooks-and-trajectory-datasets.md)

## Execution Rule

Execute one card at a time. Run the card's verification commands before starting the next card. If verification fails, stop and fix the current card instead of carrying broken assumptions forward.
