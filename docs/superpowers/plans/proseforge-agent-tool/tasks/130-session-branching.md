# Task 130: Session Branching / 会话分支

## Goal

允许从某个会话步骤创建分支，用于探索不同写作方向。

## Architecture Notes

This card belongs to the **Conversation Lifecycle** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

命令：

```bash id="mug0zj"
pf-agent session branch <session_id> --from-step 12 --name alt-ending
pf-agent session branches <session_id>
pf-agent session switch <branch_id>
```

用途：

* 同一章尝试不同改写方向
* 不同结局分支
* 不同 provider 结果对比

## Files

- Create or modify implementation files under `src/proseforge_agent/chat/` as needed for this card.
- Add focused tests in `tests/chat/test_session_branching.py`.
- Add fixtures under `tests/chat/fixtures/session-branching/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/chat/test_session_branching.py::test_session_branching_contract`**

```python
def test_session_branching_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 130 production code is not implemented yet.
    raise AssertionError("Task 130 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/chat/test_session_branching.py::test_session_branching_contract -q
```

Expected: FAIL because Task 130 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/chat/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/chat/test_session_branching.py::test_session_branching_contract -q
```

Expected: PASS with the new Task 130 behavior covered.

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
git add src/proseforge_agent/chat/ tests/chat/test_session_branching.py
git commit -m "feat: add session branching"
```

## Verification

Source DoD:

从一个历史步骤分支后，可以继续对话而不污染主 session。

---

Before closing this card, run:

```powershell
python -m pytest tests/chat/test_session_branching.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 130 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/chat/ tests/chat/test_session_branching.py
git commit -m "feat: add session branching"
```

Do not bundle adjacent task cards into this commit.
