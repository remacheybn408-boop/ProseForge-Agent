# Task 85: Chapter Reorganization / 章节重排

## Goal

支持长篇小说常见的章节移动、拆分、合并、重新编号。

## Architecture Notes

This card belongs to the **Novel Project Operations** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent chapter move ch_003 --to-volume vol_002 --after ch_010
pf-agent chapter split ch_004 --at-scene sc_004_03
pf-agent chapter merge ch_005 ch_006 --into ch_005
pf-agent chapter renumber --slug demo_novel
```

要求：

* 更新 manifest
* 更新 artifact graph
* 保留旧版本
* 生成 reorg log

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_chapter_reorganization.py`.
- Add fixtures under `tests/novel/fixtures/chapter-reorganization/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_chapter_reorganization.py::test_chapter_reorganization_contract`**

```python
def test_chapter_reorganization_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 85 production code is not implemented yet.
    raise AssertionError("Task 85 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_chapter_reorganization.py::test_chapter_reorganization_contract -q
```

Expected: FAIL because Task 85 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_chapter_reorganization.py::test_chapter_reorganization_contract -q
```

Expected: PASS with the new Task 85 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_chapter_reorganization.py
git commit -m "feat: add chapter reorganization"
```

## Verification

Source DoD:

跨卷移动章节后，manifest 和章节编号保持一致。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_chapter_reorganization.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 85 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_chapter_reorganization.py
git commit -m "feat: add chapter reorganization"
```

Do not bundle adjacent task cards into this commit.
