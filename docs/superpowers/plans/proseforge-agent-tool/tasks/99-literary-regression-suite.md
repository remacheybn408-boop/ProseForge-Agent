# Task 99: Literary Regression Suite / 文风回归测试

## Goal

防止模型、prompt、规则升级后文风跑偏。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

建立 golden samples：

```text
tests/literary/golden/
```

比较：

* 对话密度
* 标点习惯
* 叙事距离
* 句长分布
* 关键词风格
* 自定义规则命中率

命令：

```bash
pf-agent literary test --slug demo_novel
pf-agent literary baseline --slug demo_novel
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_literary_regression_suite.py`.
- Add fixtures under `tests/novel/fixtures/literary-regression-suite/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_literary_regression_suite.py::test_literary_regression_suite_contract`**

```python
def test_literary_regression_suite_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 99 production code is not implemented yet.
    raise AssertionError("Task 99 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_literary_regression_suite.py::test_literary_regression_suite_contract -q
```

Expected: FAIL because Task 99 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_literary_regression_suite.py::test_literary_regression_suite_contract -q
```

Expected: PASS with the new Task 99 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_literary_regression_suite.py
git commit -m "feat: add literary regression suite"
```

## Verification

Source DoD:

修改 prompt 后能跑 literary regression，判断风格是否明显漂移。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_literary_regression_suite.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 99 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_literary_regression_suite.py
git commit -m "feat: add literary regression suite"
```

Do not bundle adjacent task cards into this commit.
