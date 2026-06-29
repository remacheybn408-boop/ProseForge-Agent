# Task 137: Evidence Pack Retrieval / Evidence Pack 检索融合

## Goal

让 RAG 检索结果进入 evidence pack，并受上下文预算控制。

## Architecture Notes

This card belongs to the **RAG And Vector Retrieval** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

evidence pack 来源：

* manifest
* bible
* timeline
* rules
* memory
* RAG chunks
* current chapter
* related scenes

要求：

* token budget aware
* deduplicate
* source attribution
* ranking score
* project scope isolation

## Files

- Create or modify implementation files under `src/proseforge_agent/retrieval/` as needed for this card.
- Add focused tests in `tests/retrieval/test_evidence_pack_retrieval.py`.
- Add fixtures under `tests/retrieval/fixtures/evidence-pack-retrieval/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/retrieval/test_evidence_pack_retrieval.py::test_evidence_pack_retrieval_contract`**

```python
def test_evidence_pack_retrieval_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 137 production code is not implemented yet.
    raise AssertionError("Task 137 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/retrieval/test_evidence_pack_retrieval.py::test_evidence_pack_retrieval_contract -q
```

Expected: FAIL because Task 137 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/retrieval/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/retrieval/test_evidence_pack_retrieval.py::test_evidence_pack_retrieval_contract -q
```

Expected: PASS with the new Task 137 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/retrieval/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/retrieval/ tests/retrieval/test_evidence_pack_retrieval.py
git commit -m "feat: add evidence pack retrieval"
```

## Verification

Source DoD:

写章节时，系统能自动检索相关 bible / timeline / 旧章节片段，并注入 evidence pack。

---

Before closing this card, run:

```powershell
python -m pytest tests/retrieval/test_evidence_pack_retrieval.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 137 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/retrieval/ tests/retrieval/test_evidence_pack_retrieval.py
git commit -m "feat: add evidence pack retrieval"
```

Do not bundle adjacent task cards into this commit.
