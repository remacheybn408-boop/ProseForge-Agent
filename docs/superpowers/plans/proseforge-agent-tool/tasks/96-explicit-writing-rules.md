# Task 96: Explicit Writing Rules / 显式写作规则管理

## Goal

让用户可以显式添加写作规则，而不是只靠 review → memory 隐式学习。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent rules add "永远不使用引号，叙述只靠白描"
pf-agent rules add "低对话密度"
pf-agent rules add "禁止破折号"
pf-agent rules list
pf-agent rules remove rule_001
```

规则级别：

* global-level
* project-level
* chapter-level

规则自动注入 evidence pack。

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_explicit_writing_rules.py`.
- Add fixtures under `tests/novel/fixtures/explicit-writing-rules/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_explicit_writing_rules.py::test_explicit_writing_rules_contract`**

```python
def test_explicit_writing_rules_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 96 production code is not implemented yet.
    raise AssertionError("Task 96 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_explicit_writing_rules.py::test_explicit_writing_rules_contract -q
```

Expected: FAIL because Task 96 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_explicit_writing_rules.py::test_explicit_writing_rules_contract -q
```

Expected: PASS with the new Task 96 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_explicit_writing_rules.py
git commit -m "feat: add explicit writing rules"
```

## Verification

Source DoD:

添加规则后，后续 draft/review/rewrite 自动读取规则。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_explicit_writing_rules.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 96 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_explicit_writing_rules.py
git commit -m "feat: add explicit writing rules"
```

Do not bundle adjacent task cards into this commit.
