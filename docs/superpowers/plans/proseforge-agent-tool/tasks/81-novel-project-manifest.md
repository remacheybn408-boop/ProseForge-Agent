# Task 81: Novel Project Manifest / 小说项目总清单

## Goal

为每个小说项目建立统一的项目总清单，作为整本书的源头索引。

## Architecture Notes

This card belongs to the **Novel Project Operations** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

新增：

```text
project.manifest.yaml
```

管理：

* project slug
* title
* author
* language
* volumes
* acts
* chapters
* scenes
* drafts
* exports
* bible
* rules
* timeline
* metadata

示例：

```yaml
project:
  slug: demo_novel
  title: 示例小说
  language: zh-CN

structure:
  volumes:
    - id: vol_001
      title: 第一卷
      acts:
        - id: act_001
          chapters:
            - id: ch_001
              title: 第一章
              scenes:
                - id: sc_001
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_novel_project_manifest.py`.
- Add fixtures under `tests/novel/fixtures/novel-project-manifest/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash
pf-agent project init --slug demo_novel
pf-agent project manifest --slug demo_novel
pf-agent project validate --slug demo_novel
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_novel_project_manifest.py::test_novel_project_manifest_contract`**

```python
def test_novel_project_manifest_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 81 production code is not implemented yet.
    raise AssertionError("Task 81 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_novel_project_manifest.py::test_novel_project_manifest_contract -q
```

Expected: FAIL because Task 81 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_novel_project_manifest.py::test_novel_project_manifest_contract -q
```

Expected: PASS with the new Task 81 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_novel_project_manifest.py
git commit -m "feat: add novel project manifest"
```

## Verification

Source DoD:

```bash
pf-agent project init --slug demo_novel
```

必须生成合法 `project.manifest.yaml`。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_novel_project_manifest.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 81 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_novel_project_manifest.py
git commit -m "feat: add novel project manifest"
```

Do not bundle adjacent task cards into this commit.
