# Task 112: System Prompt Management / 系统提示管理

## Goal

让 agent 行为可控，支持系统提示模板、版本、组合和 per-session 自定义。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent prompt list
pf-agent prompt show professional_novel_editor
pf-agent prompt set --session session_001 --template cold_editor
pf-agent chat --system "你是冷酷编辑"
```

组合规则：

```text
base system prompt
+ agent profile
+ project context
+ writing rules
+ provider constraints
+ session override
```

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_system_prompt_management.py`.
- Add fixtures under `tests/agent/fixtures/system-prompt-management/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_system_prompt_management.py::test_system_prompt_management_contract`**

```python
def test_system_prompt_management_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 112 production code is not implemented yet.
    raise AssertionError("Task 112 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_system_prompt_management.py::test_system_prompt_management_contract -q
```

Expected: FAIL because Task 112 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_system_prompt_management.py::test_system_prompt_management_contract -q
```

Expected: PASS with the new Task 112 behavior covered.

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
git add src/proseforge_agent/agent/ tests/agent/test_system_prompt_management.py
git commit -m "feat: add system prompt management"
```

## Verification

Source DoD:

不同 session 可以使用不同 system prompt，并记录版本。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_system_prompt_management.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 112 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_system_prompt_management.py
git commit -m "feat: add system prompt management"
```

Do not bundle adjacent task cards into this commit.
