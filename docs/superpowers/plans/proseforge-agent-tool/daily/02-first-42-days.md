# First 42 Days

Dates use the current project date context: Friday, 2026-06-26.

## How To Use This Calendar

This is not a promise that the work must take 42 days. It is a recommended daily sequence if the project is being built carefully while also designing the professional writing workflow. If a day finishes early, continue to the next task card only after tests pass.

## Daily Plan

| Day | Date | Engineering Target | Novel-System Target | Required Output |
| --- | --- | --- | --- | --- |
| 1 | 2026-06-26 | Split plan into readable files | Define Agent product boundary | Split plan directory |
| 2 | 2026-06-27 | Task 01 package skeleton | Establish project identity | Package import test |
| 3 | 2026-06-28 | Task 02 config and workspace | Bind title, slug, workspace | Config loader test |
| 4 | 2026-06-29 | Task 03 ProseForge adapter | Confirm existing engine status | Adapter command test |
| 5 | 2026-06-30 | Task 04 provider contracts | Define model roles | Fake provider test |
| 6 | 2026-07-01 | Task 05 OpenAI-compatible adapter | Support foreign/domestic/local endpoints | Injected transport test |
| 7 | 2026-07-02 | Task 06 native/local profiles | Anthropic/Gemini/local config | Native adapter tests |
| 8 | 2026-07-03 | Task 07 memory schema | Deep memory foundation | SQLite schema test |
| 9 | 2026-07-04 | Task 08 memory ingestion | Classify durable facts | Classifier test |
| 10 | 2026-07-05 | Task 08 compaction | Merge duplicate memory | Compaction test |
| 11 | 2026-07-06 | Task 09 retrieval intent | Query planning | Router test |
| 12 | 2026-07-07 | Task 09 evidence packs | Must-keep context | Evidence test |
| 13 | 2026-07-08 | Task 10 phase planner | Stage planning | Phase plan test |
| 14 | 2026-07-09 | Task 11 daily workbook | Date-based workbook | Workbook test |
| 15 | 2026-07-10 | Task 11 recommendation logic | Tomorrow recommendation | State-to-next test |
| 16 | 2026-07-11 | Task 12 workflow state | Save and load runs | State test |
| 17 | 2026-07-12 | Task 12 recovery | Retry failed steps | Recovery test |
| 18 | 2026-07-13 | Task 13 chapter pre | Call ProseForge pre | Pre stub test |
| 19 | 2026-07-14 | Task 13 retrieval before draft | Evidence into prompt | Prompt pack test |
| 20 | 2026-07-15 | Task 13 draft save | Versioned draft artifact | Draft writer test |
| 21 | 2026-07-16 | Task 13 post/review | ProseForge quality gates | Post/review sequence test |
| 22 | 2026-07-17 | Task 14 rewrite card | ProseForge rewrite integration | Rewrite command test |
| 23 | 2026-07-18 | Task 14 rewriter provider | Targeted rewrite | Fake rewrite test |
| 24 | 2026-07-19 | Task 14 accept | Diff and accept result | Accept test |
| 25 | 2026-07-20 | Task 15 CLI basics | phase-plan and workbook commands | CLI tests |
| 26 | 2026-07-21 | Task 15 reports | Markdown and JSON reports | Renderer tests |
| 27 | 2026-07-22 | Task 16 extension registry | Register providers and steps | Registry test |
| 28 | 2026-07-23 | Task 16 docs | User guide and architecture docs | Docs written |
| 29 | 2026-07-24 | Task 17 end-to-end fake run | Whole flow without network | E2E fake test |
| 30 | 2026-07-25 | Task 17 Windows path QA | Path and UTF-8 hardening | Path tests |
| 31 | 2026-07-26 | Real engine smoke | Status and safe adapter calls | Smoke report |
| 32 | 2026-07-27 | Demo project workflow | Demo phase and daily workbook | Demo artifacts |
| 33 | 2026-07-28 | Memory stress test | Many memories and retrieval rank | Retrieval test |
| 34 | 2026-07-29 | Provider config audit | Domestic/local examples | Provider docs |
| 35 | 2026-07-30 | Failure recovery audit | Resume interrupted run | Recovery report |
| 36 | 2026-07-31 | Rewrite loop audit | No overwrite guarantee | Version test |
| 37 | 2026-08-01 | Report audit | Artifacts complete | Report sample |
| 38 | 2026-08-02 | User guide pass | Chinese instructions complete | User guide update |
| 39 | 2026-08-03 | Full pytest | Fix failures | Passing test run |
| 40 | 2026-08-04 | Demo command transcript | Copy-paste usage flow | Demo log |
| 41 | 2026-08-05 | Release candidate | Package metadata and docs | RC checklist |
| 42 | 2026-08-06 | v0.1.0 readiness | First usable Agent release | Release notes |

## Daily Closeout Standard

Every day must end with:

```markdown
## Closeout

- Date:
- Completed task cards:
- Tests run:
- Artifacts written:
- Memory decisions:
- Blockers:
- Tomorrow recommendation:
```

## Slip Policy

If a day slips:

- Do not merge two unfinished task cards.
- Carry the unfinished task forward.
- Write the reason in the closeout.
- Keep the next recommendation deterministic.

## Writing Days After Engineering Foundation

Once Task 13 is complete, daily workbooks switch from engineering-first to writing-first:

1. Read yesterday's closeout.
2. Run or inspect `pre`.
3. Retrieve evidence.
4. Draft or rewrite.
5. Run `post`.
6. Run `review`.
7. Update memory.
8. Generate tomorrow recommendation.
