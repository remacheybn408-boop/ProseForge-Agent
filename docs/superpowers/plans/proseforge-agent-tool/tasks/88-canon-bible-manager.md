# Task 88: Canon Bible Manager / 显式设定 Bible

## Goal

建立可编辑、可冻结、可引用的小说设定 Bible。Memory 不能替代 Bible。

## Architecture Notes

This card belongs to the **Canon And Story Intelligence** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

管理：

* characters
* locations
* factions
* items
* rules
* worldbuilding
* terminology

文件结构：

```text
bible/
  characters.yaml
  locations.yaml
  factions.yaml
  items.yaml
  rules.yaml
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_canon_bible_manager.py`.
- Add fixtures under `tests/novel/fixtures/canon-bible-manager/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash
pf-agent bible add character --slug demo_novel
pf-agent bible list characters --slug demo_novel
pf-agent bible freeze --slug demo_novel
pf-agent bible snapshot --slug demo_novel
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_canon_bible_manager.py::test_canon_bible_manager_contract`**

```python
def test_canon_bible_manager_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 88 production code is not implemented yet.
    raise AssertionError("Task 88 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_canon_bible_manager.py::test_canon_bible_manager_contract -q
```

Expected: FAIL because Task 88 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_canon_bible_manager.py::test_canon_bible_manager_contract -q
```

Expected: PASS with the new Task 88 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_canon_bible_manager.py
git commit -m "feat: add canon bible manager"
```

## Verification

Source DoD:

写作 evidence pack 中能自动注入相关 bible 条目。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_canon_bible_manager.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 88 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_canon_bible_manager.py
git commit -m "feat: add canon bible manager"
```

Do not bundle adjacent task cards into this commit.
