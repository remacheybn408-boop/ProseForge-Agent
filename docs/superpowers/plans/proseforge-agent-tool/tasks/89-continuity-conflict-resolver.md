# Task 89: Continuity Conflict Resolver / 设定冲突仲裁

## Goal

发现设定冲突后，允许用户选择保留、废弃、合并，而不是只输出 warning。

## Architecture Notes

This card belongs to the **Canon And Story Intelligence** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

冲突类型：

* 人物年龄冲突
* 地点名称冲突
* 时间线冲突
* 人物关系冲突
* 世界规则冲突
* 物品状态冲突

命令：

```bash
pf-agent continuity check --slug demo_novel
pf-agent continuity resolve --slug demo_novel --conflict conflict_001
```

仲裁动作：

```text
keep_left
keep_right
merge
mark_intentional
defer
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_continuity_conflict_resolver.py`.
- Add fixtures under `tests/novel/fixtures/continuity-conflict-resolver/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_continuity_conflict_resolver.py::test_continuity_conflict_resolver_contract`**

```python
def test_continuity_conflict_resolver_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 89 production code is not implemented yet.
    raise AssertionError("Task 89 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_continuity_conflict_resolver.py::test_continuity_conflict_resolver_contract -q
```

Expected: FAIL because Task 89 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_continuity_conflict_resolver.py::test_continuity_conflict_resolver_contract -q
```

Expected: PASS with the new Task 89 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_continuity_conflict_resolver.py
git commit -m "feat: add continuity conflict resolver"
```

## Verification

Source DoD:

冲突解决后写入 bible / timeline / manifest，并记录 audit log。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_continuity_conflict_resolver.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 89 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_continuity_conflict_resolver.py
git commit -m "feat: add continuity conflict resolver"
```

Do not bundle adjacent task cards into this commit.
