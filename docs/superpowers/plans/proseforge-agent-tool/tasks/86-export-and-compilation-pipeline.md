# Task 86: Export / Compilation Pipeline / 小说导出与编译

## Goal

实现整本书导出功能，把多章合并为完整 book artifact。

## Architecture Notes

This card belongs to the **Novel Project Operations** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

```bash
pf-agent export --slug demo_novel --format txt
pf-agent export --slug demo_novel --format markdown
pf-agent export --slug demo_novel --format pdf
pf-agent export --slug demo_novel --format epub
```

支持：

* 按卷导出
* 按章范围导出
* 包含/排除草稿
* 生成目录
* 生成页码
* front matter
* back matter
* copyright page

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_export_and_compilation_pipeline.py`.
- Add fixtures under `tests/novel/fixtures/export-and-compilation-pipeline/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_export_and_compilation_pipeline.py::test_export_and_compilation_pipeline_contract`**

```python
def test_export_and_compilation_pipeline_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 86 production code is not implemented yet.
    raise AssertionError("Task 86 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_export_and_compilation_pipeline.py::test_export_and_compilation_pipeline_contract -q
```

Expected: FAIL because Task 86 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_export_and_compilation_pipeline.py::test_export_and_compilation_pipeline_contract -q
```

Expected: PASS with the new Task 86 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_export_and_compilation_pipeline.py
git commit -m "feat: add export and compilation pipeline"
```

## Verification

Source DoD:

```bash
pf-agent export --slug demo_novel --format txt
```

必须生成完整 book artifact。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_export_and_compilation_pipeline.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 86 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_export_and_compilation_pipeline.py
git commit -m "feat: add export and compilation pipeline"
```

Do not bundle adjacent task cards into this commit.
