# Task 125: Offline Mode / 离线模式

## Goal

支持无网络状态下使用 ProseForge Agent 的本地能力。

## Architecture Notes

This card belongs to the **Resilience And Offline Operation** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

离线模式允许：

* project doctor
* manifest validate
* export txt/markdown
* search keyword
* stats
* backup
* fake provider chat
* local memory read

离线模式禁用：

* remote provider call
* MCP network tools
* model catalog update
* cloud sync

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_offline_mode.py`.
- Add fixtures under `tests/agent/fixtures/offline-mode/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="fsxdgf"
pf-agent --offline chat --provider fake
pf-agent offline status
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_offline_mode.py::test_offline_mode_contract`**

```python
def test_offline_mode_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 125 production code is not implemented yet.
    raise AssertionError("Task 125 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_offline_mode.py::test_offline_mode_contract -q
```

Expected: FAIL because Task 125 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_offline_mode.py::test_offline_mode_contract -q
```

Expected: PASS with the new Task 125 behavior covered.

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
git add src/proseforge_agent/agent/ tests/agent/test_offline_mode.py
git commit -m "feat: add offline mode"
```

## Verification

Source DoD:

断网环境下，`pf-agent --offline doctor` 和 `pf-agent export --format txt` 可运行。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_offline_mode.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 125 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_offline_mode.py
git commit -m "feat: add offline mode"
```

Do not bundle adjacent task cards into this commit.
