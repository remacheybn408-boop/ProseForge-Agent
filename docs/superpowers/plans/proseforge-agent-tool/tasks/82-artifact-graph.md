# Task 82: Artifact Graph / 稿件产物依赖图

## Goal

建立 artifact 依赖关系：outline → scene beats → draft → review → revision → final → export。

## Architecture Notes

This card belongs to the **Novel Project Operations** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

新增 artifact graph：

```text
artifacts.graph.yaml
```

记录：

* artifact id
* artifact type
* source artifact
* generated artifact
* dependency
* checksum
* created_at
* provider
* prompt version

示例：

```yaml
artifacts:
  - id: draft_ch_001_v1
    type: draft
    depends_on:
      - outline_ch_001
      - bible_snapshot_001
```

## Files

- Create or modify implementation files under `src/proseforge_agent/novel/` as needed for this card.
- Add focused tests in `tests/novel/test_artifact_graph.py`.
- Add fixtures under `tests/novel/fixtures/artifact-graph/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash
pf-agent artifacts list --slug demo_novel
pf-agent artifacts graph --slug demo_novel
pf-agent artifacts trace draft_ch_001_v1
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/novel/test_artifact_graph.py::test_artifact_graph_contract`**

```python
def test_artifact_graph_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 82 production code is not implemented yet.
    raise AssertionError("Task 82 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/novel/test_artifact_graph.py::test_artifact_graph_contract -q
```

Expected: FAIL because Task 82 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/novel/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/novel/test_artifact_graph.py::test_artifact_graph_contract -q
```

Expected: PASS with the new Task 82 behavior covered.

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
git add src/proseforge_agent/novel/ tests/novel/test_artifact_graph.py
git commit -m "feat: add artifact graph"
```

## Verification

Source DoD:

任意 draft/review/revision/export 都能追溯来源。

---

Before closing this card, run:

```powershell
python -m pytest tests/novel/test_artifact_graph.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 82 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/novel/ tests/novel/test_artifact_graph.py
git commit -m "feat: add artifact graph"
```

Do not bundle adjacent task cards into this commit.
