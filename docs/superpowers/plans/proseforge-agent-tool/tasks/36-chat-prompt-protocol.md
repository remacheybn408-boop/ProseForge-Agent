# Task 36: Chat Prompt Protocol

## Goal

Define prompt contracts for general chat, project chat, workflow chat, operator chat, and creative chat.

## Agent Product Requirement

The agent needs consistent behavior across chat modes while still allowing provider-specific routing.

## Architecture Notes

`ChatPromptBuilder` is a pure prompt-assembly module. It takes a mode, the user text, an evidence pack, and a permission ceiling, and returns a structured prompt pack. It does not call providers, memory, retrieval, or the network; the Agent Kernel (Task 31) owns those calls and passes the assembled evidence in. The builder must keep canon facts (`must_keep`) visually and structurally separate from agent suggestions so a downstream model cannot blur the two.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md (Product Modes, Chat Prompt sections)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/chat/prompts.py`
- Create `tests/test_chat_prompt_protocol.py`
- Create `tests/fixtures/chat-prompt-protocol/evidence_pack.json`

## Interfaces / Contracts

- `ChatPromptBuilder(project_slug: str | None).build(mode: str, user_text: str, evidence_pack: EvidencePack | None, permission_ceiling: str) -> PromptPack`.
- `PromptPack` fields: `mode`, `role`, `system_policy`, `canon_section` (from `evidence_pack.must_keep`), `suggestion_section`, `permission_ceiling`, `output_expectations`, `messages` (provider-ready `list[dict[str, str]]`).
- Canon items and suggestion items never share a section; canon items carry their source ids.
- Unknown mode raises `ConfigurationError`; the five supported modes are `general_chat`, `project_chat`, `workflow_chat`, `operator_chat`, `creative_chat`.

## Data Flow

1. Validate the requested mode against the five supported modes.
2. Select the role and system policy template for that mode.
3. Place `evidence_pack.must_keep` items into the canon section with source ids.
4. Place remaining retrieved/derived context into the suggestion section.
5. Apply the permission ceiling note so the model knows which actions it may propose.
6. Render the ordered `messages` list and return the `PromptPack`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_chat_prompt_protocol.py::test_project_chat_prompt_separates_canon_from_suggestions`**

```python
def test_project_chat_prompt_separates_canon_from_suggestions(evidence_pack):
    pack = ChatPromptBuilder(project_slug="demo").build(
        mode="project_chat",
        user_text="今天写什么？",
        evidence_pack=evidence_pack,
        permission_ceiling="read_only",
    )
    canon_ids = {item["source_id"] for item in pack.canon_section}
    suggestion_ids = {item["source_id"] for item in pack.suggestion_section}
    assert canon_ids  # at least one must_keep fact is surfaced as canon
    assert canon_ids.isdisjoint(suggestion_ids)
    assert pack.permission_ceiling == "read_only"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_chat_prompt_protocol.py::test_project_chat_prompt_separates_canon_from_suggestions -q
```

Expected: FAIL because `ChatPromptBuilder` and `PromptPack` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ChatPromptBuilder`, `PromptPack`, the per-mode system policy templates, and the canon/suggestion split.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_chat_prompt_protocol.py::test_project_chat_prompt_separates_canon_from_suggestions -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_general_chat_prompt_has_no_project_canon_section
test_unknown_mode_raises_configuration_error
test_workflow_chat_prompt_includes_active_run_summary
test_permission_ceiling_note_blocks_write_proposals_when_read_only
test_prompt_messages_round_trip_utf8_chinese_text
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_chat_prompt_protocol.py -q
pf-agent chat --message "今天写什么？" --project demo --provider fake --show-prompt
```

Expected: tests pass and `--show-prompt` prints a prompt pack whose canon and suggestion sections are clearly separated.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/prompts.py tests/test_chat_prompt_protocol.py tests/fixtures/chat-prompt-protocol
git commit -m "feat: add chat prompt protocol"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Prompt text and evidence are UTF-8 and must round-trip Chinese characters.
- Source ids are opaque strings, never absolute file paths.
- No drive letters or home-directory assumptions in templates or fixtures.

## Failure Modes To Prove

- Unknown mode raises `ConfigurationError` before any prompt is built.
- Empty evidence pack still produces a valid prompt with an empty canon section, not a crash.
- A `read_only` ceiling produces a system note that forbids proposing write actions.
- Canon facts are never copied into the suggestion section.

## Verification

```powershell
python -m pytest tests/test_chat_prompt_protocol.py -q
pf-agent chat --message "今天写什么？" --project demo --provider fake --show-prompt
```

## Acceptance

- All five chat modes produce a valid prompt pack.
- Canon and suggestion content stay in separate sections with source ids on canon.
- The builder performs no provider, memory, or network calls.
- Permission ceiling is reflected in the system policy.

## Commit Boundary

Commit only the chat prompt files and tests after verification passes. Do not add provider, memory, or retrieval changes here.
