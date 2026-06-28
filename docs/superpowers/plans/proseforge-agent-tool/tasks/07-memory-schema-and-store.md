# Task 07: Memory Schema And Store

## Goal

Create the durable schema and local store for long-form novel memory.

## Architecture Notes

Memory is auditable project state, not prompt scratch text.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/memory/schema.py`
- Create `src/proseforge_agent/memory/store.py`
- Create `tests/test_memory_schema.py`
- Create `tests/test_memory_store.py`
- Create `tests/fixtures/memory/items.jsonl`

## Interfaces / Contracts

`MemoryItem` has id, project_slug, type, text, source, confidence, tags, status, supersedes, created_at, updated_at. `MemoryStore` supports add, get, list, supersede, export.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_memory_store.py::test_memory_item_can_be_added_and_superseded`**

```python
def test_memory_item_can_be_added_and_superseded(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    first = store.add(MemoryItem(project_slug="demo", type="canon_fact", text="Hero fears water", source="manual"))
    second = store.supersede(first.id, text="Hero fears deep water")
    assert store.get(first.id).status == "superseded"
    assert store.get(second.id).supersedes == first.id
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_memory_store.py::test_memory_item_can_be_added_and_superseded -q
```

Expected: FAIL because memory schema and store are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement dataclasses, SQLite tables, status transitions, JSON export, and source-reference validation.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_memory_store.py::test_memory_item_can_be_added_and_superseded -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_memory_schema.py tests/test_memory_store.py -q
pf-agent memory list --project demo --store .pf-agent/memory.sqlite
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/memory/schema.py tests
git commit -m "feat: add memory schema and store"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_memory_schema.py tests/test_memory_store.py -q
pf-agent memory list --project demo --store .pf-agent/memory.sqlite
```

## Acceptance

- Accepted and superseded facts remain auditable.
- Missing source references fail validation.
- Store writes are transaction protected.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
