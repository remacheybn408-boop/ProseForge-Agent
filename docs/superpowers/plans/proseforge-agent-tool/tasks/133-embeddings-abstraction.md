# Task 133: Embeddings Abstraction / 向量嵌入抽象层

## Goal

为 RAG 增加 embeddings 抽象层，支持本地和远程 embedding provider。

## Architecture Notes

This card belongs to the **RAG And Vector Retrieval** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持 provider：

* fake embedding
* local sentence-transformers 预留
* OpenAI embeddings
* Qwen embeddings 预留
* custom HTTP embedding provider

内部接口：

```python id="s1p5h1"
EmbeddingProvider
embed_text(text)
embed_batch(texts)
```

配置：

```yaml id="3et9tc"
embeddings:
  provider: fake
  dimension: 384
```

## Files

- Create or modify implementation files under `src/proseforge_agent/retrieval/` as needed for this card.
- Add focused tests in `tests/retrieval/test_embeddings_abstraction.py`.
- Add fixtures under `tests/retrieval/fixtures/embeddings-abstraction/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/retrieval/test_embeddings_abstraction.py::test_embeddings_abstraction_contract`**

```python
def test_embeddings_abstraction_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 133 production code is not implemented yet.
    raise AssertionError("Task 133 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/retrieval/test_embeddings_abstraction.py::test_embeddings_abstraction_contract -q
```

Expected: FAIL because Task 133 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/retrieval/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/retrieval/test_embeddings_abstraction.py::test_embeddings_abstraction_contract -q
```

Expected: PASS with the new Task 133 behavior covered.

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
git add src/proseforge_agent/retrieval/ tests/retrieval/test_embeddings_abstraction.py
git commit -m "feat: add embeddings abstraction"
```

## Verification

Source DoD:

同一段文本能通过 embedding provider 得到向量并写入索引。

---

Before closing this card, run:

```powershell
python -m pytest tests/retrieval/test_embeddings_abstraction.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 133 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/retrieval/ tests/retrieval/test_embeddings_abstraction.py
git commit -m "feat: add embeddings abstraction"
```

Do not bundle adjacent task cards into this commit.
