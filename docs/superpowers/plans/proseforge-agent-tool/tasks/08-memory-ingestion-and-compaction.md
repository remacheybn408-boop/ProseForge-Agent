# Task 08: Memory Ingestion And Compaction

## Goal

Ingest ProseForge artifacts into reviewable memory candidates and compact them without source loss.

## Architecture Notes

Raw project material enters memory through candidates first; canon changes require review.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/memory/ingest.py`
- Create `src/proseforge_agent/memory/compact.py`
- Create `src/proseforge_agent/memory/review.py`
- Create `tests/test_memory_ingestion.py`
- Create `tests/test_memory_compaction.py`
- Create `tests/fixtures/proseforge_project/`

## Interfaces / Contracts

`IngestionCandidate` records source_path, source_kind, extracted_text, proposed_type, confidence, reason. `CompactionReport` records included ids, excluded ids, summary id, and source coverage.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_memory_ingestion.py::test_ingest_chapter_creates_review_candidates_with_sources`**

```python
def test_ingest_chapter_creates_review_candidates_with_sources(tmp_path):
    chapter = tmp_path / "chapter-001.md"
    chapter.write_text("# Chapter 1\nA promise is made at the old bridge.", encoding="utf-8")
    candidates = ArtifactIngestor().scan_file(chapter, project_slug="demo")
    assert candidates[0].source_path == chapter
    assert candidates[0].status == "candidate"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_memory_ingestion.py::test_ingest_chapter_creates_review_candidates_with_sources -q
```

Expected: FAIL because ingestion classes are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement artifact scanners, candidate creation, review status transitions, compaction summaries, duplicate detection, and compaction reports.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_memory_ingestion.py::test_ingest_chapter_creates_review_candidates_with_sources -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_memory_ingestion.py tests/test_memory_compaction.py -q
pf-agent memory ingest --project demo --source tests/fixtures/proseforge_project --dry-run
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/memory/ingest.py tests
git commit -m "feat: add memory ingestion and compaction"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_memory_ingestion.py tests/test_memory_compaction.py -q
pf-agent memory ingest --project demo --source tests/fixtures/proseforge_project --dry-run
```

## Acceptance

- Dry-run writes nothing.
- Every candidate has a source and reason.
- Compaction summaries retain links to all source ids.
- Contradictions are preserved instead of hidden.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
