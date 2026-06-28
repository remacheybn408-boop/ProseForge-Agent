# Task 34: Chat Session Store

## Goal

Persist chat sessions, transcripts, retrieved evidence references, tool decisions, and memory candidates.

## Agent Product Requirement

The agent must remember conversations across restarts and let users resume general, project, workflow, operator, and creative chats.

## Architecture Notes

Session storage is portable JSON metadata plus JSONL transcripts. It should work in project-local `.pf-agent/` mode and native app-data mode.

## Files

- Create `src/proseforge_agent/chat/session.py`
- Create `src/proseforge_agent/chat/transcript.py`
- Create `tests/test_chat_session_store.py`
- Create `tests/fixtures/chat/session_messages.jsonl`

## Interfaces / Contracts

- `ChatSession(id, mode, project_slug, workflow_run_id, title, created_at, updated_at, messages_path)`.
- `ChatMessage(role, content, created_at, evidence_refs, tool_calls, provider_metadata)`.
- `ChatSessionStore.create()`, `append_message()`, `list()`, `load_context()`, `export_markdown()`, `export_json()`.

## Data Flow

1. Choose workspace or native app-data chat directory.
2. Create session metadata.
3. Append messages as JSONL.
4. Load compact context for the kernel.
5. Export transcript for reports, diagnostics, and user review.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_session_store.py::test_session_store_round_trips_utf8_messages`**

```python
def test_session_store_round_trips_utf8_messages(tmp_path):
    store = ChatSessionStore(tmp_path)
    session = store.create(mode="project_chat", project_slug="demo")
    store.append_message(session.id, role="user", content="今天写什么？")
    context = store.load_context(session.id)
    assert context.messages[-1].content == "今天写什么？"
    assert context.session.project_slug == "demo"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_session_store.py::test_session_store_round_trips_utf8_messages -q
```

Expected: FAIL because `ChatSessionStore` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement session id generation, metadata writing, JSONL append, UTF-8 reads, context loading, and project filtering.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_session_store.py::test_session_store_round_trips_utf8_messages -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

Required tests:

```text
test_list_sessions_filters_by_project
test_export_markdown_contains_tool_decisions
test_corrupt_message_line_is_reported_not_silently_dropped
test_session_paths_are_relative_to_workspace
test_load_context_limits_messages_without_losing_last_user_turn
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_session_store.py -q
pf-agent chat sessions --project demo
```

Expected: command exits 0 and lists session id, mode, project, updated time, and title.

## Cross-Platform Notes

- Store transcripts as UTF-8 JSONL.
- Use `Path` objects for paths with spaces.
- Line endings must not affect JSONL parsing.
- Export Markdown must preserve Chinese text.

## Failure Modes To Prove

- Corrupt JSONL line creates a recoverable warning.
- Missing session id returns a controlled error.
- Read-only export does not modify transcript files.

## Verification

```powershell
python -m pytest tests/test_chat_session_store.py -q
pf-agent chat sessions --project demo
```

## Acceptance

- Chat sessions survive process restart.
- Session transcripts can be exported.
- Project chat sessions are filterable by project.
- Evidence refs and tool decisions are preserved.
- Session files are portable between Windows, macOS, and Linux.

## Commit Boundary

Commit chat session files and tests only after verification passes.
