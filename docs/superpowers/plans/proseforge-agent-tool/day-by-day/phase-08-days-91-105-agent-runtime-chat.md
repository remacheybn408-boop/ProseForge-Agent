# Phase 08: Agent Runtime And Chat

Dates: 2026-09-24 to 2026-10-08.

Goal: turn ProseForge Agent from a workflow tool into a conversational agent runtime.

## Day 91: 2026-09-24, Agent Runtime Kernel

Primary objective: implement Task 31 so every user turn flows through one Agent Kernel.

Expected outputs: `AgentKernel`, turn request/result contracts, event trace, fake-provider chat turn.

Verification:

```powershell
python -m pytest tests/test_agent_kernel.py -q
pf-agent chat --message "hello" --provider fake --no-project
```

Acceptance: general chat works without project state, and the turn writes a transcript plus trace id.

## Day 92: 2026-09-25, Intent Router And Modes

Primary objective: implement Task 32 for general, project, workflow, operator, and creative chat modes.

Expected outputs: conversation mode enum, intent enum, deterministic classifier, fixture suite.

Verification:

```powershell
python -m pytest tests/test_intent_router.py -q
pf-agent chat classify --mode operator_chat --text "provider key 读不到"
```

Acceptance: ambiguous write requests ask for clarification instead of running tools.

## Day 93: 2026-09-26, Tool Registry And Permissions

Primary objective: implement Task 33 to prevent chat from unsafe mutations.

Expected outputs: tool registry, permission policy, audit events, deny/confirm decisions.

Verification:

```powershell
python -m pytest tests/test_agent_tools_permissions.py -q
pf-agent tools list --include-permissions
```

Acceptance: read-only chat cannot accept chapters, change secrets, or install shell integration.

## Day 94: 2026-09-27, Chat Session Store

Primary objective: implement Task 34 for durable chat transcripts.

Expected outputs: session metadata, JSONL transcript store, Markdown/JSON export.

Verification:

```powershell
python -m pytest tests/test_chat_session_store.py -q
pf-agent chat sessions --project demo
```

Acceptance: UTF-8 Chinese messages round-trip and sessions survive process restart.

## Day 95: 2026-09-28, Chat CLI REPL

Primary objective: implement Task 35 so users can talk to the agent directly.

Expected outputs: `pf-agent chat`, one-shot mode, REPL mode, slash commands.

Verification:

```powershell
python -m pytest tests/test_chat_cli_repl.py -q
pf-agent chat --message "hello" --provider fake
```

Acceptance: chat works without a novel project and saves a session transcript.

## Day 96: 2026-09-29, Chat Prompt Protocol

Primary objective: implement Task 36 so each chat mode has a clear prompt contract.

Expected outputs: prompt builder, mode-specific policy sections, permission ceiling in prompts.

Verification:

```powershell
python -m pytest tests/test_chat_prompt_protocol.py -q
pf-agent doctor --section chat-prompt-protocol
```

Acceptance: project chat separates hard canon from suggestions and warnings.

## Day 97: 2026-09-30, Chat Retrieval And Citations

Primary objective: implement Task 37 so project chat answers with cited evidence.

Expected outputs: chat retrieval responder, memory/report citations, answer rendering.

Verification:

```powershell
python -m pytest tests/test_chat_retrieval_citations.py -q
pf-agent chat --project demo --message "昨天写到哪里了？" --provider fake
```

Acceptance: project chat never states canon without source references.

## Day 98: 2026-10-01, Chat Memory And Preferences

Primary objective: implement Task 38 for durable user preferences and project decisions.

Expected outputs: chat memory extractor, global preference candidates, project memory candidates.

Verification:

```powershell
python -m pytest tests/test_chat_memory_preferences.py -q
pf-agent memory review --project demo --status candidate
```

Acceptance: chat can create memory candidates but cannot silently accept canon.

## Day 99: 2026-10-02, Chat-To-Workflow Handoff

Primary objective: implement Task 39 so chat can propose workflow actions safely.

Expected outputs: handoff package, confirmation flag, workflow target metadata.

Verification:

```powershell
python -m pytest tests/test_chat_workflow_handoff.py -q
pf-agent chat --project demo --message "帮我继续第 3 章，但先说明风险" --provider fake
```

Acceptance: workflow action requires a handoff package and permission check.

## Day 100: 2026-10-03, Event Bus And Background Jobs

Primary objective: implement Task 40 for traceable agent events and safe background work.

Expected outputs: event bus, trace ids, background job reports.

Verification:

```powershell
python -m pytest tests/test_agent_events_jobs.py -q
pf-agent workflow trace --project demo --last
```

Acceptance: chat, workflow, provider, retrieval, and install actions emit traceable events.

## Day 101: 2026-10-04, Chat Mode Integration Drill

Primary objective: run all chat modes through fake provider and fake tools.

Expected outputs: mode drill report with five chat modes.

Verification:

```powershell
pf-agent chat drill --all-modes --provider fake --write-report
```

Acceptance: every mode has a transcript, intent decision, permission decision, and event trace.

## Day 102: 2026-10-05, Chat Failure Drill

Primary objective: prove chat recovers from provider failure, retrieval failure, and denied tool calls.

Expected outputs: failure drill report and regression tests.

Verification:

```powershell
python -m pytest tests/test_agent_kernel.py tests/test_chat_cli_repl.py -q
pf-agent chat drill --scenario provider_timeout --write-report
```

Acceptance: failure responses include recovery advice and trace ids.

## Day 103: 2026-10-06, Chat Documentation

Primary objective: document chat modes, slash commands, memory behavior, and workflow handoff.

Expected outputs: operator chat guide and examples.

Verification:

```powershell
pf-agent docs check-examples --section chat
```

Acceptance: docs show general chat, project chat, operator chat, and workflow handoff.

## Day 104: 2026-10-07, Chat Cross-Platform Smoke

Primary objective: simulate Windows, macOS, and Linux chat sessions.

Expected outputs: cross-platform chat smoke report.

Verification:

```powershell
python -m pytest tests/test_chat_session_store.py tests/test_platform_io.py -q
pf-agent chat --message "中文路径和空格路径测试" --provider fake
```

Acceptance: UTF-8, spaces in paths, and session exports pass on simulated platforms.

## Day 105: 2026-10-08, Phase 08 Integration Gate

Primary objective: prove Agent Kernel and chat are release-gate features.

Expected outputs: Phase 08 closeout report.

Verification:

```powershell
python -m pytest tests/test_agent_kernel.py tests/test_intent_router.py tests/test_chat_cli_repl.py -q
pf-agent chat drill --all-modes --provider fake --write-report
```

Acceptance: the product can be used as a chat agent, not only a writing workflow runner.
