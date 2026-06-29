# Task 80: First Run Bootstrap / 首次运行自动引导

## Goal

用户第一次运行 `pf-agent chat` 时，如果还没 setup，不应该直接报错，而是引导 setup。

## Architecture Notes

This card belongs to the **Setup Completion** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

当检测到：

* config 不存在
* setup.completed != true
* workspace 不存在
* default provider 不可用

输出：

```text
ProseForge Agent 尚未完成初始化。

推荐：
  pf-agent setup --quick

零配置验证：
  pf-agent setup --minimal
```

交互终端询问：

```text
是否现在进入 setup？[Y/n]
```

CI / non-interactive 模式只输出错误和修复命令，不弹 prompt。

## Files

- Create or modify implementation files under `src/proseforge_agent/setup/` as needed for this card.
- Add focused tests in `tests/setup/test_first_run_bootstrap.py`.
- Add fixtures under `tests/setup/fixtures/first-run-bootstrap/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/setup/test_first_run_bootstrap.py::test_first_run_bootstrap_contract`**

```python
def test_first_run_bootstrap_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 80 production code is not implemented yet.
    raise AssertionError("Task 80 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/setup/test_first_run_bootstrap.py::test_first_run_bootstrap_contract -q
```

Expected: FAIL because Task 80 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/setup/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/setup/test_first_run_bootstrap.py::test_first_run_bootstrap_contract -q
```

Expected: PASS with the new Task 80 behavior covered.

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
git add src/proseforge_agent/setup/ tests/setup/test_first_run_bootstrap.py
git commit -m "feat: add first run bootstrap"
```

## Verification

Source DoD:

删除 config 后运行：

```bash
pf-agent chat --message "hello"
```

必须显示 setup 引导，而不是 Python traceback。

---

Before closing this card, run:

```powershell
python -m pytest tests/setup/test_first_run_bootstrap.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 80 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/setup/ tests/setup/test_first_run_bootstrap.py
git commit -m "feat: add first run bootstrap"
```

Do not bundle adjacent task cards into this commit.
