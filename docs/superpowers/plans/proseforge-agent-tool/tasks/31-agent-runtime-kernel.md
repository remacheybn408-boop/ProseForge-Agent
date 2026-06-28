# Task 31: Agent Runtime Kernel

## Goal

Build the per-turn Agent Kernel that powers chat, workflow control, install help, provider diagnosis, and future user surfaces.

## Agent Product Requirement

ProseForge Agent must feel like a real agent, not a collection of unrelated commands. Every user turn should pass through one durable loop that can classify intent, retrieve context, ask permission, call tools, respond, save memory candidates, and write trace events.

## Architecture Notes

The kernel orchestrates subsystems but does not own their business logic. It calls the intent router, permission policy, retrieval planner, provider router, tool registry, memory manager, chat session store, and event bus through interfaces.

Because everything is injected, this card depends on those subsystems' *interfaces*, not their concrete implementations. The tests therefore use `fake_session_store`, `fake_tools`, `fake_provider`, and `fake_retrieval` fixtures (defined in this card's test module / `conftest.py`) rather than the concrete Tool Registry (Task 33) or Chat Session Store (Task 34), which are implemented later. This keeps Task 31 executable first without a forward dependency on Tasks 33–34.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/kernel.py`
- Create `src/proseforge_agent/agent/types.py`
- Create `tests/test_agent_kernel.py`
- Create `tests/fixtures/agent/kernel_turn.json`

## Interfaces / Contracts

- `AgentTurnRequest(session_id, text, mode, project_slug, permission_level)` is the only kernel input.
- `AgentTurnResult(text, intent, tool_calls, evidence_refs, memory_candidate_ids, events)` is the only kernel output.
- `AgentKernel.run_turn()` accepts injected fake provider, fake tools, fake retrieval, and fake session store.
- Kernel responses must include a trace id for diagnostics.

## Data Flow

1. Load or create chat session.
2. Classify user intent.
3. Resolve maximum permission level.
4. Retrieve evidence when the intent requires context.
5. Select provider role or internal tool.
6. Execute the allowed action.
7. Persist transcript, events, and memory candidates.
8. Return user-facing text and machine-readable turn metadata.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_agent_kernel.py::test_kernel_runs_read_only_chat_turn_without_project`**

```python
def test_kernel_runs_read_only_chat_turn_without_project(fake_provider, fake_tools, fake_session_store):
    kernel = AgentKernel(
        provider=fake_provider,
        tools=fake_tools,
        session_store=fake_session_store,
    )
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="new",
            text="hello",
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )
    )
    assert result.intent.name == "answer_directly"
    assert result.tool_calls == []
    assert result.text
    assert result.events
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_agent_kernel.py::test_kernel_runs_read_only_chat_turn_without_project -q
```

Expected: FAIL because `AgentKernel`, `AgentTurnRequest`, and `AgentTurnResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement typed request/result objects, constructor dependency injection, read-only direct-answer path, trace id creation, event recording, and transcript append.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_agent_kernel.py::test_kernel_runs_read_only_chat_turn_without_project -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

Required tests:

```text
test_kernel_retrieves_evidence_for_project_question
test_kernel_blocks_write_tool_when_permission_is_read_only
test_kernel_records_provider_failure_as_event
test_kernel_returns_recovery_message_when_tool_fails
test_kernel_saves_memory_candidate_for_durable_user_preference
```

- [ ] **Step 6: Run subsystem verification**

Run:

```powershell
python -m pytest tests/test_agent_kernel.py -q
pf-agent chat --message "hello" --provider fake --no-project
```

Expected: tests pass and the one-shot chat returns text without requiring a project.

- [ ] **Step 7: Run cross-platform contract check**

Run:

```powershell
python -m pytest tests/test_agent_kernel.py -q
```

Expected: PASS for UTF-8 content, relative transcript paths, and path-with-spaces fixture cases.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/agent tests/test_agent_kernel.py tests/fixtures/agent
git commit -m "feat: add agent runtime kernel"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Store transcript paths relative to the configured workspace or native app data directory.
- Use UTF-8 for all chat text and event records.
- Never assume a drive letter, home directory format, shell type, or path separator.

## Failure Modes To Prove

- Provider timeout returns a readable response with trace id.
- Permission denial does not call the denied tool.
- Missing session creates a new session only when mode permits it.
- Event write failure does not mark the user request as completed.

## Verification

```powershell
python -m pytest tests/test_agent_kernel.py -q
pf-agent chat --message "hello" --provider fake --no-project
```

## Acceptance

- General chat works without a novel project.
- Project chat can request evidence through the kernel.
- Kernel does not import concrete provider implementations directly.
- Every turn writes an event trace.
- Kernel result can be rendered by CLI chat, future TUI, future desktop UI, and local API.

## Commit Boundary

Commit only Agent Kernel files and tests after verification passes.
