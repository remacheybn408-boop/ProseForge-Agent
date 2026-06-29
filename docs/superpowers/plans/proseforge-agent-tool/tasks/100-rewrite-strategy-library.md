# Task 100: Rewrite Strategy Library / 改稿策略库

## Goal

把 rewrite 从单一命令扩展为可选择策略的改稿系统。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

策略：

* expand
* condense
* lower_dialogue
* enhance_description
* increase_tension
* simplify_language
* yu_hua_plain_narration
* remove_quotes
* reduce_exposition

命令：

```bash
pf-agent rewrite --strategy condense --chapter ch_001
pf-agent rewrite --strategy lower_dialogue --chapter ch_001
pf-agent rewrite strategies list
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_rewrite_strategy_library.py`.
- Add fixtures under `tests/novel/fixtures/rewrite-strategy-library/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_rewrite_strategy_library.py::test_rewrite_strategy_library_contract`**

```python
def test_rewrite_strategy_library_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 100 production code is not implemented yet.
    raise AssertionError("Task 100 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_rewrite_strategy_library.py::test_rewrite_strategy_library_contract -q
```

Expected: FAIL because Task 100 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_rewrite_strategy_library.py::test_rewrite_strategy_library_contract -q
```

Expected: PASS with the new Task 100 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_rewrite_strategy_library.py
git commit -m "feat: add rewrite strategy library"
```

## Verification

Source DoD:

同一章节可以用不同策略生成不同 revision artifact。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_rewrite_strategy_library.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 100 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_rewrite_strategy_library.py
git commit -m "feat: add rewrite strategy library"
```

Do not bundle adjacent task cards into this commit.
