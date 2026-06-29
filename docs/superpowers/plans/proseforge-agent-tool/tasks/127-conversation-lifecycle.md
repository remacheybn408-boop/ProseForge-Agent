# Task 127: Conversation Lifecycle / 会话生命周期管理

## Goal

管理对话 session 的创建、归档、清理、恢复、删除。

## Architecture Notes

This card belongs to the **Conversation Lifecycle** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

session 状态：

* active
* archived
* pinned
* deleted
* branched

命令：

```bash id="70cfml"
pf-agent session list
pf-agent session show <id>
pf-agent session archive <id>
pf-agent session restore <id>
pf-agent session delete <id>
pf-agent session cleanup --older-than 90d
```

## Files

- Create or modify implementation files under `src/proseforge_agent/chat/` as needed for this card.
- Add focused tests in `tests/chat/test_conversation_lifecycle.py`.
- Add fixtures under `tests/chat/fixtures/conversation-lifecycle/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/chat/test_conversation_lifecycle.py::test_conversation_lifecycle_contract`**

```python
def test_conversation_lifecycle_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 127 production code is not implemented yet.
    raise AssertionError("Task 127 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/chat/test_conversation_lifecycle.py::test_conversation_lifecycle_contract -q
```

Expected: FAIL because Task 127 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/chat/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/chat/test_conversation_lifecycle.py::test_conversation_lifecycle_contract -q
```

Expected: PASS with the new Task 127 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/chat/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/chat/ tests/chat/test_conversation_lifecycle.py
git commit -m "feat: add conversation lifecycle"
```

## Verification

Source DoD:

用户可以归档旧会话，并从归档中恢复。

---

Before closing this card, run:

```powershell
python -m pytest tests/chat/test_conversation_lifecycle.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 127 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/chat/ tests/chat/test_conversation_lifecycle.py
git commit -m "feat: add conversation lifecycle"
```

Do not bundle adjacent task cards into this commit.
