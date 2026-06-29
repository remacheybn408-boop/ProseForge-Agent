# Task 111: Context Window Management / 上下文窗口管理

## Goal

支持长对话和长篇小说场景下的上下文预算管理。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

能力：

* provider tokenizer
* token budget estimation
* context window usage report
* evidence pack budget
* automatic truncation
* early conversation summarization
* provider-specific max context

命令：

```bash
pf-agent context status
pf-agent context compact --session session_001
```

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_context_window_management.py`.
- Add fixtures under `tests/agent/fixtures/context-window-management/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_context_window_management.py::test_context_window_management_contract`**

```python
def test_context_window_management_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 111 production code is not implemented yet.
    raise AssertionError("Task 111 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_context_window_management.py::test_context_window_management_contract -q
```

Expected: FAIL because Task 111 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_context_window_management.py::test_context_window_management_contract -q
```

Expected: PASS with the new Task 111 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/agent/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_context_window_management.py
git commit -m "feat: add context window management"
```

## Verification

Source DoD:

构建 prompt 前能输出当前 token 占用和剩余预算。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_context_window_management.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 111 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_context_window_management.py
git commit -m "feat: add context window management"
```

Do not bundle adjacent task cards into this commit.
