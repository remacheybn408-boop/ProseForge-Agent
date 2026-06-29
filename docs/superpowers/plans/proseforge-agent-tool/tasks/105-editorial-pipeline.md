# Task 105: Editorial Pipeline / 编辑工序流水线

## Goal

把 review/rewrite 拆成真正的小说编辑流程。

## Architecture Notes

This card belongs to the **Writing Quality And Editorial Systems** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

阶段：

```text
outline
rough_draft
structure_edit
style_edit
continuity_check
copy_edit
final
```

命令：

```bash
pf-agent editorial run --slug demo_novel --chapter ch_001
pf-agent editorial status --slug demo_novel
pf-agent editorial promote --chapter ch_001 --to final
```

要求：

* 每个阶段都有 artifact
* 每个阶段有 DoD
* 高风险 promote 需要 approval

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_editorial_pipeline.py`.
- Add fixtures under `tests/novel/fixtures/editorial-pipeline/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_editorial_pipeline.py::test_editorial_pipeline_contract`**

```python
def test_editorial_pipeline_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 105 production code is not implemented yet.
    raise AssertionError("Task 105 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_editorial_pipeline.py::test_editorial_pipeline_contract -q
```

Expected: FAIL because Task 105 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_editorial_pipeline.py::test_editorial_pipeline_contract -q
```

Expected: PASS with the new Task 105 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_editorial_pipeline.py
git commit -m "feat: add editorial pipeline"
```

## Verification

Source DoD:

章节能从 rough_draft 推进到 final，并保留每阶段产物。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_editorial_pipeline.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 105 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_editorial_pipeline.py
git commit -m "feat: add editorial pipeline"
```

Do not bundle adjacent task cards into this commit.
