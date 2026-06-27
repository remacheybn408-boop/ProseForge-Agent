# Phase 03: Deep Memory And Retrieval

Dates: 2026-07-20 to 2026-08-01.

Goal: build long-horizon novel memory that can ingest, classify, compact, retrieve, cite, and update information automatically.

## Day 25: 2026-07-20, Memory Schema

Primary objective: define the memory schema for professional fiction production.

Context to read:

- `tasks/07-memory-schema-and-store.md`
- `architecture/04-deep-memory-and-retrieval.md`
- `appendices/01-data-contracts.md`

Work blocks:

- Morning: define memory item types: canon fact, character profile, relationship, location, timeline event, foreshadowing seed, unresolved promise, style rule, market insight, editorial decision, chapter summary, scene beat, contradiction, and discarded idea.
- Midday: define fields: stable id, project slug, volume, chapter, scene, source artifact, evidence quote pointer, confidence, freshness, privacy class, tags, embedding id, supersedes id, and review status.
- Afternoon: implement schema validation and migration version field.
- Closeout: write tests for required fields, invalid enum values, source pointers, and version migration.

Expected outputs:

- Memory schema.
- Memory validation tests.
- Schema documentation.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory schema --print
```

Acceptance checklist:

- The schema supports both writing craft and continuity tracking.
- Each memory item can be traced back to a source.
- Old memory can be superseded without being silently deleted.
- The schema is versioned for future migrations.

Stop condition:

- Stop when memory items are structured enough for retrieval and review.

## Day 26: 2026-07-21, Local Memory Store

Primary objective: implement a local durable memory store.

Context to read:

- `tasks/07-memory-schema-and-store.md`
- Memory schema from Day 25.

Work blocks:

- Morning: choose local store implementation consistent with the repo stack, with JSONL or SQLite for facts and an embedding index abstraction for vectors.
- Midday: implement create, read, update, supersede, list, query-by-tag, query-by-source, and export operations.
- Afternoon: add file-lock or transaction strategy for safe workflow updates.
- Closeout: test persistence across process restarts.

Expected outputs:

- Memory store implementation.
- Store tests.
- Export command.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory add --project demo --type canon_fact --text "主角怕水" --source manual
pf-agent memory list --project demo
```

Acceptance checklist:

- Memory persists after the CLI exits.
- Superseded items remain auditable.
- Concurrent writes do not corrupt the store.
- Export output can be read by a human editor.

Stop condition:

- Stop when memory can survive real workflow execution.

## Day 27: 2026-07-22, Ingestion From ProseForge Artifacts

Primary objective: ingest existing ProseForge outputs into structured memory.

Context to read:

- `tasks/08-memory-ingestion-and-compaction.md`
- `architecture/03-proseforge-engine-integration.md`

Work blocks:

- Morning: identify source artifacts: project bible, outlines, chapter drafts, reports, guard results, exports, and editorial notes.
- Midday: implement source scanners that produce ingestion candidates with source pointers.
- Afternoon: implement deterministic extraction rules for chapter title, chapter summary, characters mentioned, locations, timeline markers, and open questions.
- Closeout: test ingestion on fixture project files.

Expected outputs:

- Artifact scanners.
- Ingestion candidate model.
- Fixture tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory ingest --project demo --source fixtures/proseforge_demo --dry-run
```

Acceptance checklist:

- Dry-run lists memory candidates without writing them.
- Each candidate has a source artifact and reason.
- Unsupported file types are skipped with a clear warning.
- Existing ProseForge artifacts are treated as source of truth.

Stop condition:

- Stop when old project material can enter the memory pipeline safely.

## Day 28: 2026-07-23, LLM-Assisted Memory Classification

Primary objective: classify ingestion candidates into useful memory types with model assistance.

Context to read:

- `tasks/08-memory-ingestion-and-compaction.md`
- Provider router files from Phase 02.

Work blocks:

- Morning: write classification prompt contract that returns structured memory items, uncertainty, contradictions, and suggested tags.
- Midday: implement classifier using provider role `memory` and fake provider fixture outputs.
- Afternoon: add tests for clean classification, ambiguous classification, contradiction detection, and refusal fallback.
- Closeout: add CLI dry-run output showing before and after classification.

Expected outputs:

- Memory classifier.
- Prompt contract.
- Tests and dry-run command.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory classify --project demo --dry-run
```

Acceptance checklist:

- The classifier never writes unreviewed low-confidence facts as canon.
- Contradictions become memory items of type `contradiction`.
- The fake provider can test classifier behavior deterministically.
- Classification includes confidence and evidence references.

Stop condition:

- Stop when model-assisted memory is useful but not blindly trusted.

## Day 29: 2026-07-24, Memory Review Queue

Primary objective: add a human-review gate for canon-sensitive memory.

Context to read:

- `architecture/04-deep-memory-and-retrieval.md`
- Memory classification outputs.

Work blocks:

- Morning: implement review statuses: candidate, accepted, rejected, needs_merge, superseded, and archived.
- Midday: add commands to list, accept, reject, merge, and supersede memory candidates.
- Afternoon: add tests for status transitions and audit log entries.
- Closeout: generate a review report for a fixture ingestion run.

Expected outputs:

- Review queue commands.
- Audit log.
- Review report.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory review --project demo --status candidate
```

Acceptance checklist:

- Canon facts require acceptance before being used as hard constraints.
- Rejected memory remains auditable.
- Merges preserve all source pointers.
- Review reports are understandable by a novelist or editor.

Stop condition:

- Stop when memory has editorial governance.

## Day 30: 2026-07-25, Embedding And Vector Index

Primary objective: add semantic retrieval while preserving exact-source traceability.

Context to read:

- `tasks/09-retrieval-router-and-evidence-packs.md`
- Provider role definitions for embedding.

Work blocks:

- Morning: implement embedding provider interface and local vector index abstraction.
- Midday: support batch embedding, idempotent embedding updates, deleted-item handling, and index rebuild.
- Afternoon: add tests for indexing, nearest-neighbor query, stale embedding detection, and provider failure fallback.
- Closeout: run a fixture semantic query.

Expected outputs:

- Embedding interface.
- Vector index abstraction.
- Semantic query tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory index --project demo
pf-agent memory search --project demo --query "主角为什么害怕水"
```

Acceptance checklist:

- Search results include memory item id, score, source pointer, and summary.
- Index rebuild is deterministic for fake embeddings.
- Provider failures do not corrupt existing indexes.
- Exact metadata remains available after vector search.

Stop condition:

- Stop when semantic retrieval can support chapter drafting.

## Day 31: 2026-07-26, Hybrid Retrieval

Primary objective: combine semantic, keyword, recency, and graph-like retrieval signals.

Context to read:

- `tasks/09-retrieval-router-and-evidence-packs.md`
- Memory schema and vector index.

Work blocks:

- Morning: implement keyword retrieval over tags, names, locations, and source paths.
- Midday: implement ranking blend: semantic score, exact match score, recency, canon priority, unresolved-promise priority, and contradiction penalty.
- Afternoon: add tests for queries that require exact names, vague themes, recent chapter context, and old canon facts.
- Closeout: print retrieval explanation for each result.

Expected outputs:

- Hybrid retriever.
- Ranking explanation.
- Retrieval tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent retrieve --project demo --query "女主和哥哥的旧约定" --explain
```

Acceptance checklist:

- Exact names are not lost to semantic similarity.
- Canon facts outrank speculative notes when relevant.
- Retrieval explains inclusion and exclusion.
- Contradictions are surfaced when relevant.

Stop condition:

- Stop when retrieval can explain itself to a writer.

## Day 32: 2026-07-27, Evidence Pack Builder

Primary objective: turn retrieval results into prompt-ready evidence packs.

Context to read:

- `architecture/04-deep-memory-and-retrieval.md`
- Hybrid retrieval output.

Work blocks:

- Morning: define evidence pack sections: hard canon, current chapter context, active arcs, character constraints, world rules, style rules, unresolved promises, contradictions, and optional market notes.
- Midday: implement token-budgeted evidence packing with source references.
- Afternoon: add tests for token limits, duplicate collapse, stale memory exclusion, contradiction inclusion, and source citation formatting.
- Closeout: generate one evidence pack for a demo chapter.

Expected outputs:

- Evidence pack builder.
- Token-budget tests.
- CLI evidence output.

Verification:

```powershell
python -m pytest -q tests
pf-agent evidence --project demo --chapter 1 --role drafter --print
```

Acceptance checklist:

- Evidence packs are concise enough for model prompts.
- Hard canon is clearly separated from suggestions.
- Every included item has a source reference.
- Excluded high-score items can be explained.

Stop condition:

- Stop when workflows can request evidence by role.

## Day 33: 2026-07-28, Memory Compaction

Primary objective: prevent long projects from drowning in raw memory.

Context to read:

- `tasks/08-memory-ingestion-and-compaction.md`
- Evidence pack builder.

Work blocks:

- Morning: define compaction rules for chapter summaries, character state summaries, arc summaries, style summaries, and market feedback summaries.
- Midday: implement compaction job that creates summary memories while preserving source ranges.
- Afternoon: add tests for no-source-loss, supersede behavior, confidence inheritance, and conflict preservation.
- Closeout: compare evidence pack before and after compaction.

Expected outputs:

- Memory compactor.
- Compaction tests.
- Compaction report.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory compact --project demo --dry-run
```

Acceptance checklist:

- Compaction reduces prompt load without erasing auditability.
- Source ranges remain inspectable.
- Contradictions are not hidden inside summaries.
- Accepted canon cannot be overwritten by low-confidence summaries.

Stop condition:

- Stop when memory can scale beyond a short demo.

## Day 34: 2026-07-29, Automatic Retrieval Hooks

Primary objective: make workflows retrieve the right context automatically.

Context to read:

- `tasks/09-retrieval-router-and-evidence-packs.md`
- Workflow architecture.

Work blocks:

- Morning: define retrieval intents for planning, drafting, reviewing, rewriting, memory update, and daily workbook generation.
- Midday: implement retrieval router that maps workflow step plus chapter metadata to query templates and evidence pack format.
- Afternoon: add tests for each workflow intent using fake memory.
- Closeout: instrument retrieval logs for later debugging.

Expected outputs:

- Retrieval router.
- Workflow retrieval intent tests.
- Retrieval log format.

Verification:

```powershell
python -m pytest -q tests
pf-agent retrieve auto --project demo --intent chapter_draft --chapter 1 --explain
```

Acceptance checklist:

- Workflows do not require manual search queries for common steps.
- Auto queries include character, plot, timeline, style, and open-promise context.
- Retrieval logs show query text, selected items, skipped items, and token budget.
- The router can be overridden by a human.

Stop condition:

- Stop when retrieval is automatic but transparent.

## Day 35: 2026-07-30, Memory Update After Drafting

Primary objective: update memory from newly generated chapters and editorial decisions.

Context to read:

- Memory ingestion and review queue.
- Chapter workflow design.

Work blocks:

- Morning: define post-draft memory extraction targets: new facts, changed character state, new promises, resolved promises, timeline events, location changes, and style observations.
- Midday: implement post-draft extraction and candidate creation.
- Afternoon: add tests for new fact, resolved promise, contradiction, and rejected candidate.
- Closeout: generate a memory update report from a fixture chapter.

Expected outputs:

- Post-draft memory updater.
- Update report.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory update-from-chapter --project demo --chapter 1 --dry-run
```

Acceptance checklist:

- New chapter content does not silently change canon.
- The update report separates accepted facts, candidates, contradictions, and questions.
- Promise resolution is tracked.
- The workflow can pause for human review when canon changes.

Stop condition:

- Stop when chapter generation can feed long-term memory safely.

## Day 36: 2026-07-31, Memory Quality Audit

Primary objective: audit memory for contradictions, stale facts, duplicates, and missing sources.

Context to read:

- `appendices/02-test-matrix.md`
- Memory store and compaction outputs.

Work blocks:

- Morning: implement audit checks for missing source, duplicate fact, conflicting canon, stale summary, orphan embedding, and unresolved promise age.
- Midday: add audit report command with severity levels.
- Afternoon: add tests for each audit category.
- Closeout: run audit on demo memory.

Expected outputs:

- Memory audit engine.
- Audit report.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory audit --project demo --write-report
```

Acceptance checklist:

- Audit findings include severity, affected item ids, and suggested resolution.
- The report is useful to a writer, not only an engineer.
- Audits do not mutate memory unless a separate fix command is used.
- Missing source references fail the audit gate.

Stop condition:

- Stop when memory quality can be measured.

## Day 37: 2026-08-01, Phase 03 Integration Gate

Primary objective: prove deep memory and retrieval are ready for professional writing workflows.

Context to read:

- All Phase 03 files.
- Memory audit report.

Work blocks:

- Morning: run memory tests, retrieval tests, and fake-provider classification tests.
- Midday: run end-to-end fixture: ingest, classify, review, index, retrieve, build evidence pack, compact, audit.
- Afternoon: fix schema or report issues found by the fixture.
- Closeout: write Phase 03 closeout report and Phase 04 start context.

Expected outputs:

- Passing memory test suite.
- Evidence pack example.
- Memory audit report.
- Phase 03 closeout report.

Verification:

```powershell
python -m pytest -q
pf-agent memory ingest --project demo --source fixtures/proseforge_demo --dry-run
pf-agent evidence --project demo --chapter 1 --role drafter --print
pf-agent memory audit --project demo --write-report
```

Acceptance checklist:

- Memory can ingest existing ProseForge artifacts.
- Retrieval can automatically build cited evidence packs.
- Memory can compact without source loss.
- Audit detects contradictions and missing sources.
- Phase 04 can consume memory for planning and daily workbooks.

Stop condition:

- Stop when memory is a dependable subsystem, not a prompt appendix.
