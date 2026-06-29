# Task 83: Bulk Import / 批量导入已有稿件

## Goal

支持把已有完整手稿导入 ProseForge Agent，并自动分章、映射到 project manifest。

## Architecture Notes

This card belongs to the **Novel Project Operations** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持格式：

* txt
* markdown
* docx
* folder of chapters

能力：

* 自动识别章节标题
* 自动生成 chapter id
* 自动写入 manifest
* 原稿保留为 raw import artifact
* 允许人工确认分章结果

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_bulk_import.py`.
- Add fixtures under `tests/novel/fixtures/bulk-import/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash
pf-agent import manuscript ./novel.txt --slug demo_novel
pf-agent import manuscript ./chapters/ --slug demo_novel
pf-agent import preview ./novel.txt
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_bulk_import.py::test_bulk_import_contract`**

```python
def test_bulk_import_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 83 production code is not implemented yet.
    raise AssertionError("Task 83 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_bulk_import.py::test_bulk_import_contract -q
```

Expected: FAIL because Task 83 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_bulk_import.py::test_bulk_import_contract -q
```

Expected: PASS with the new Task 83 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_bulk_import.py
git commit -m "feat: add bulk import"
```

## Verification

Source DoD:

导入一个 txt 后，系统能生成 chapters 和 manifest 映射。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_bulk_import.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 83 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_bulk_import.py
git commit -m "feat: add bulk import"
```

Do not bundle adjacent task cards into this commit.
