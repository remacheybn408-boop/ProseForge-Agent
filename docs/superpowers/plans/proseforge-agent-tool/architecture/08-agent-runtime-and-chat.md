# Agent Runtime And Chat Architecture

## Goal

ProseForge Agent must be a general agent runtime with professional novel-writing workflows as one major capability. It must also support direct conversation, project-aware chat, memory-backed advice, and handoff from chat into executable workflows.

## Product Modes

| Mode | Purpose | Example |
| --- | --- | --- |
| `general_chat` | Talk with the user without requiring a novel project. | "帮我分析这个角色设定是否有冲突。" |
| `project_chat` | Chat with access to one project, memory, plans, reports, and workflow state. | "昨天写到哪里了？今天应该做什么？" |
| `workflow_chat` | Chat while controlling or explaining a workflow run. | "继续第 3 章的改稿，但先告诉我风险。" |
| `operator_chat` | Help install, configure, diagnose, and route providers. | "为什么 Qwen provider 认证失败？" |
| `creative_chat` | Brainstorm, review style, discuss market direction, and preserve useful decisions. | "这个开头够不够抓人？" |

## Runtime Components

```text
User Surface
  -> Chat Session Manager
  -> Intent Router
  -> Agent Kernel
      -> Tool Registry
      -> Permission Policy
      -> Retrieval Planner
      -> Memory Manager
      -> Provider Router
      -> Workflow Bridge
      -> Report Renderer
      -> Event Bus
```

## Chat Session Manager

Responsibilities:

- Create and resume sessions.
- Bind a session to no project, one project, or one workflow run.
- Store user messages, assistant messages, tool decisions, retrieved evidence, and workflow handoffs.
- Keep short-term context separate from long-term memory.
- Export session transcripts as Markdown and JSON.

Required session fields:

```json
{
  "session_id": "chat_20260627_001",
  "mode": "project_chat",
  "project_slug": "demo_novel",
  "workflow_run_id": "",
  "title": "Chapter 3 planning chat",
  "created_at": "2026-06-27T10:00:00+08:00",
  "updated_at": "2026-06-27T10:20:00+08:00",
  "messages_path": ".pf-agent/chats/chat_20260627_001/messages.jsonl",
  "memory_updates_path": ".pf-agent/chats/chat_20260627_001/memory_candidates.jsonl"
}
```

## Intent Router

The router classifies each user turn into one of these intents:

- `answer_directly`
- `retrieve_context`
- `update_memory_candidate`
- `start_workflow`
- `continue_workflow`
- `explain_artifact`
- `configure_provider`
- `diagnose_installation`
- `switch_mode`
- `ask_clarifying_question`

The router must return both the intent and the reason. It must not execute tools directly. Execution belongs to the Agent Kernel after permission checks.

## Agent Kernel

The kernel owns the per-turn loop:

1. Load session state.
2. Classify intent.
3. Resolve permission policy.
4. Retrieve memory and project evidence when needed.
5. Select provider role.
6. Call model provider or tool.
7. Render response.
8. Store transcript.
9. Create memory candidates when the conversation contains durable facts or preferences.
10. Emit events for reports and diagnostics.

## Tool Registry And Permissions

Tools are internal callable actions:

- `memory.search`
- `memory.add_candidate`
- `workflow.start`
- `workflow.continue`
- `chapter.prepare`
- `chapter.run`
- `provider.certify`
- `install.doctor`
- `report.render`

Permission levels:

| Level | Meaning |
| --- | --- |
| `read_only` | Can inspect memory, reports, plans, provider status, and workflow state. |
| `draft_write` | Can write drafts, chats, workbooks, and memory candidates. |
| `project_write` | Can update workflow state, accept chapters, and write project reports. |
| `engine_write` | Can call ProseForge mutating commands. |
| `system_write` | Can install shell completions, launchers, or service files. |

Default chat mode starts at `read_only`. Any higher level must be explicit in command flags, config policy, or an interactive confirmation.

## Chat Memory

Chat creates three memory layers:

- Session memory: what has been said in this chat.
- Project memory candidates: facts, preferences, decisions, contradictions, and unresolved questions extracted from chat.
- Global user preferences: language, style, privacy preferences, preferred model providers, and install choices.

No chat message becomes accepted canon automatically. Canon-sensitive items enter the same review queue as chapter extraction.

## Chat-To-Workflow Handoff

Chat can start or continue workflows only through a handoff package:

```json
{
  "handoff_id": "handoff_001",
  "from_session_id": "chat_20260627_001",
  "target_workflow": "chapter_lifecycle",
  "project_slug": "demo_novel",
  "chapter_no": 3,
  "intent_summary": "Draft chapter 3 with stronger opening hook.",
  "evidence_pack_id": "evidence_003",
  "permission_required": "draft_write",
  "human_confirmation": true
}
```

## Acceptance Criteria

- `pf-agent chat` works without an existing novel project.
- `pf-agent chat --project <slug>` can retrieve project context and cite sources.
- Chat can create memory candidates but cannot silently overwrite canon.
- Chat can explain what it wants to do before starting a workflow.
- Chat session transcripts are portable across Windows, macOS, and Linux.
- The same Agent Kernel powers CLI chat, future TUI, future desktop UI, and future local HTTP API.
