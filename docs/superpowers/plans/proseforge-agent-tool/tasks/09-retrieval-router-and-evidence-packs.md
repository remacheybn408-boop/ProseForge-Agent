# Task 09: Retrieval Router And Evidence Packs

## Goal

Build automatic retrieval and prompt-ready evidence packs for planning, drafting, review, and rewrite roles.

## Architecture Notes

The workflow should ask for context by intent; writers should not hand-build search queries for normal steps.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/retrieval/index.py`
- Create `src/proseforge_agent/retrieval/router.py`
- Create `src/proseforge_agent/retrieval/evidence.py`
- Create `tests/test_retrieval_router.py`
- Create `tests/test_evidence_pack.py`

## Interfaces / Contracts

`RetrievalRequest(project_slug, intent, chapter_no, query, token_budget)` returns ranked `EvidenceItem` objects with score, source, reason_included, reason_excluded. `EvidencePack` separates hard canon, active arcs, style rules, warnings, and optional market notes.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_evidence_pack.py::test_evidence_pack_keeps_canon_and_warnings_separate`**

```python
def test_evidence_pack_keeps_canon_and_warnings_separate(memory_store):
    pack = EvidencePackBuilder(memory_store).build(project_slug="demo", intent="chapter_draft", chapter_no=3, token_budget=1200)
    assert "hard_canon" in pack.sections
    assert "risk_warnings" in pack.sections
    assert all(item.source for item in pack.items)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_evidence_pack.py::test_evidence_pack_keeps_canon_and_warnings_separate -q
```

Expected: FAIL because retrieval and evidence builders are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement keyword and semantic hooks, ranking explanations, intent-to-query mapping, token-budget packing, and cited Markdown/JSON rendering.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_evidence_pack.py::test_evidence_pack_keeps_canon_and_warnings_separate -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_retrieval_router.py tests/test_evidence_pack.py -q
pf-agent evidence --project demo --chapter 1 --role drafter --print
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/retrieval/index.py tests
git commit -m "feat: add retrieval router and evidence packs"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_retrieval_router.py tests/test_evidence_pack.py -q
pf-agent evidence --project demo --chapter 1 --role drafter --print
```

## Acceptance

- Each included item has a source and inclusion reason.
- Skipped high-score items can be explained.
- Evidence packs fit the requested token budget.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
