# Task 79: Setup Recovery / 重新配置与修复

## Goal

让 setup 可重复执行，支持重新配置、追加 provider、修复坏配置。

## Architecture Notes

This card belongs to the **Setup Completion** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent setup --reconfigure
pf-agent setup --add-provider
pf-agent setup --add-provider deepseek
pf-agent setup --repair
pf-agent setup --print-config
```

要求：

* 不删除 workspace。
* 不删除 drafts。
* 不删除 memory。
* 不删除 agent.db。
* 修改配置前自动备份旧 config。
* provider key 无效不阻塞 setup。

## Files

- Create or modify implementation files under `src/proseforge_agent/setup/` as needed for this card.
- Add focused tests in `tests/setup/test_setup_recovery.py`.
- Add fixtures under `tests/setup/fixtures/setup-recovery/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/setup/test_setup_recovery.py::test_setup_recovery_contract`**

```python
def test_setup_recovery_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 79 production code is not implemented yet.
    raise AssertionError("Task 79 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/setup/test_setup_recovery.py::test_setup_recovery_contract -q
```

Expected: FAIL because Task 79 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/setup/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/setup/test_setup_recovery.py::test_setup_recovery_contract -q
```

Expected: PASS with the new Task 79 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/setup/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_setup_recovery.py
git commit -m "feat: add setup recovery"
```

## Verification

Source DoD:

```bash
pf-agent setup --minimal
pf-agent setup --add-provider deepseek
pf-agent setup --reconfigure
pf-agent setup --repair
```

均可执行，且不破坏已有数据。

---

Before closing this card, run:

```powershell
python -m pytest tests/setup/test_setup_recovery.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 79 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_setup_recovery.py
git commit -m "feat: add setup recovery"
```

Do not bundle adjacent task cards into this commit.
