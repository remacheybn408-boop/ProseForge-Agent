# Task 115: Audit Trail & Debuggability / 审计追踪与调试

## Goal

当 Agent 做错事时，用户能追踪完整决策链，而不是靠猜。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

记录每轮：

* input
* selected intent
* system prompt version
* evidence pack
* tool choice
* tool args
* tool result
* provider
* latency
* token usage
* model output
* final action

命令：

```bash
pf-agent debug session session_001
pf-agent debug step session_001 --step 3
pf-agent debug replay session_001
```

要求：

* secrets 必须脱敏
* 可导出 markdown/json
* 支持 session replay

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_audit_trail_and_debuggability.py`.
- Add fixtures under `tests/agent/fixtures/audit-trail-and-debuggability/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_audit_trail_and_debuggability.py::test_audit_trail_and_debuggability_contract`**

```python
def test_audit_trail_and_debuggability_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 115 production code is not implemented yet.
    raise AssertionError("Task 115 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_audit_trail_and_debuggability.py::test_audit_trail_and_debuggability_contract -q
```

Expected: FAIL because Task 115 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_audit_trail_and_debuggability.py::test_audit_trail_and_debuggability_contract -q
```

Expected: PASS with the new Task 115 behavior covered.

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
git add src/proseforge_agent/agent/ tests/agent/test_audit_trail_and_debuggability.py
git commit -m "feat: add audit trail and debuggability"
```

## Verification

Source DoD:

任意一次 agent 运行后，都能查看为什么调用某个工具、用了哪些 evidence、输出了什么。

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_audit_trail_and_debuggability.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 115 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_audit_trail_and_debuggability.py
git commit -m "feat: add audit trail and debuggability"
```

Do not bundle adjacent task cards into this commit.
