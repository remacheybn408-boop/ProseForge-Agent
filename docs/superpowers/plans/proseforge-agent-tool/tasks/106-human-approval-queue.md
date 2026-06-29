# Task 106: Human Approval Queue / 人类审批队列

## Goal

所有高风险动作进入审批队列，防止 Agent 自主破坏稿件。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

高风险动作：

* 覆盖 draft
* 删除 artifact
* 接受设定变更
* 解决冲突
* 批量重排章节
* 导出 final
* 回滚版本
* 修改 global rules

命令：

```bash
pf-agent approval list
pf-agent approval show approval_001
pf-agent approval approve approval_001
pf-agent approval reject approval_001
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_human_approval_queue.py`.
- Add fixtures under `tests/novel/fixtures/human-approval-queue/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_human_approval_queue.py::test_human_approval_queue_contract`**

```python
def test_human_approval_queue_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 106 production code is not implemented yet.
    raise AssertionError("Task 106 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_human_approval_queue.py::test_human_approval_queue_contract -q
```

Expected: FAIL because Task 106 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_human_approval_queue.py::test_human_approval_queue_contract -q
```

Expected: PASS with the new Task 106 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/novel/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_human_approval_queue.py
git commit -m "feat: add human approval queue"
```

## Verification

Source DoD:

高风险动作默认不直接执行，必须进入 approval queue。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_human_approval_queue.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 106 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_human_approval_queue.py
git commit -m "feat: add human approval queue"
```

Do not bundle adjacent task cards into this commit.
