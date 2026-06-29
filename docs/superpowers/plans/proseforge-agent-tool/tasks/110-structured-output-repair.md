# Task 110: Structured Output Repair / 结构化输出修复

## Goal

处理模型返回坏 JSON、半截 JSON、字段缺失、schema 不匹配等问题。

## Architecture Notes

This card belongs to the **Agent Protocol, Prompt, Context, And Audit** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

能力：

* JSON parse retry
* schema validation
* partial repair
* semantic validation
* retry prompt
* max repair attempts
* failure report

内部 API：

```python
repair_structured_output(raw_text, schema)
validate_or_repair(raw_text, schema)
```

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_structured_output_repair.py`.
- Add fixtures under `tests/agent/fixtures/structured-output-repair/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_structured_output_repair.py::test_structured_output_repair_contract`**

```python
def test_structured_output_repair_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 110 production code is not implemented yet.
    raise AssertionError("Task 110 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_structured_output_repair.py::test_structured_output_repair_contract -q
```

Expected: FAIL because Task 110 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_structured_output_repair.py::test_structured_output_repair_contract -q
```

Expected: PASS with the new Task 110 behavior covered.

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
git add src/proseforge_agent/agent/ tests/agent/test_structured_output_repair.py
git commit -m "feat: add structured output repair"
```

## Verification

Source DoD:

模型返回半坏 JSON 时，系统能自动修复或给出结构化错误。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_structured_output_repair.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 110 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_structured_output_repair.py
git commit -m "feat: add structured output repair"
```

Do not bundle adjacent task cards into this commit.
