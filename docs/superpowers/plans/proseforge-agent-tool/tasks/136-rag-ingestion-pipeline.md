# Task 136: RAG Ingestion Pipeline / RAG 入库流水线

## Goal

把项目稿件、bible、timeline、rules、导入资料切片后写入检索索引。

## Architecture Notes

This card belongs to the **RAG And Vector Retrieval** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持 ingest：

* manuscript
* chapters
* scenes
* bible
* timeline
* rules
* imported files
* session summaries

切片字段：

* chunk id
* source type
* project slug
* chapter id
* scene id
* text
* checksum
* embedding status

命令：

```bash id="a7a0rl"
pf-agent rag ingest --slug demo_novel
pf-agent rag ingest-file ./research.md --slug demo_novel
pf-agent rag status --slug demo_novel
```

## Files

- Create or modify implementation files under `src/proseforge_agent/retrieval/` as needed for this card.
- Add focused tests in `tests/retrieval/test_rag_ingestion_pipeline.py`.
- Add fixtures under `tests/retrieval/fixtures/rag-ingestion-pipeline/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/retrieval/test_rag_ingestion_pipeline.py::test_rag_ingestion_pipeline_contract`**

```python
def test_rag_ingestion_pipeline_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 136 production code is not implemented yet.
    raise AssertionError("Task 136 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/retrieval/test_rag_ingestion_pipeline.py::test_rag_ingestion_pipeline_contract -q
```

Expected: FAIL because Task 136 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/retrieval/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/retrieval/test_rag_ingestion_pipeline.py::test_rag_ingestion_pipeline_contract -q
```

Expected: PASS with the new Task 136 behavior covered.

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
git add src/proseforge_agent/retrieval/ tests/retrieval/test_rag_ingestion_pipeline.py
git commit -m "feat: add rag ingestion pipeline"
```

## Verification

Source DoD:

项目内容变更后，可以重新 ingest，只更新 checksum 变化的 chunk。

---

Before closing this card, run:

```powershell
python -m pytest tests/retrieval/test_rag_ingestion_pipeline.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 136 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/retrieval/ tests/retrieval/test_rag_ingestion_pipeline.py
git commit -m "feat: add rag ingestion pipeline"
```

Do not bundle adjacent task cards into this commit.
