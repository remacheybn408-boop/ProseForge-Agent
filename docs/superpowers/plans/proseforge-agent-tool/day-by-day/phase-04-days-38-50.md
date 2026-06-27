# Phase 04: Professional Novel Planning System

Dates: 2026-08-02 to 2026-08-14.

Goal: generate phase plans and daily writing workbooks that turn a novel project into a repeatable professional workflow.

## Day 38: 2026-08-02, Novel Project Intake

Primary objective: define and implement structured intake for a fiction project.

Context to read:

- `tasks/10-phase-plan-generator.md`
- `architecture/01-product-scope.md`
- `daily/01-daily-workbook-system.md`

Work blocks:

- Morning: define intake fields: genre, target market, target length, chapter length, update cadence, audience, tone, selling points, taboo content, comparable works, platform strategy, and author constraints.
- Midday: implement intake schema and CLI command.
- Afternoon: add tests for required fields, optional fields, defaults, and invalid values.
- Closeout: generate one demo intake file.

Expected outputs:

- Project intake schema.
- Intake CLI.
- Demo intake.

Verification:

```powershell
python -m pytest -q tests
pf-agent project intake --project demo --print-template
```

Acceptance checklist:

- Intake captures both creative and market constraints.
- The schema can evolve without breaking old projects.
- Intake output can feed phase planning and daily workbook generation.
- Missing critical fields produce clear prompts.

Stop condition:

- Stop when planning has enough input to be professional.

## Day 39: 2026-08-03, Market And Genre Planning Layer

Primary objective: make the plan sensitive to genre and platform expectations.

Context to read:

- Intake schema.
- Memory type `market_insight`.

Work blocks:

- Morning: define market-analysis prompt contract for reader promise, pacing expectation, trope inventory, risk points, title direction, and platform fit.
- Midday: implement market analysis step using provider role `market_analyst` with fake provider fixtures.
- Afternoon: add tests for genre-specific output structure and safety around uncertain market claims.
- Closeout: add market insights into memory as reviewable items.

Expected outputs:

- Market analysis module.
- Market memory ingestion.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent plan market --project demo --dry-run
```

Acceptance checklist:

- Market advice is labeled as strategy, not canon.
- The plan records uncertainty and source assumptions.
- Genre expectations influence later phase plans.
- The output is specific enough to guide chapter planning.

Stop condition:

- Stop when the agent can plan for readers, not just plot.

## Day 40: 2026-08-04, Volume And Arc Planning

Primary objective: generate volume-level and arc-level production plans.

Context to read:

- `tasks/10-phase-plan-generator.md`
- Memory evidence pack for planning.

Work blocks:

- Morning: define volume plan schema: volumes, arcs, turning points, promises, reveals, emotional movement, word-count range, chapter range, and acceptance gates.
- Midday: implement plan generator using planner role and evidence pack.
- Afternoon: add tests for schema compliance, missing intake, inconsistent chapter count, and fake provider output repair.
- Closeout: generate demo volume plan.

Expected outputs:

- Volume plan generator.
- Plan schema tests.
- Demo volume plan.

Verification:

```powershell
python -m pytest -q tests
pf-agent phase-plan --project demo --level volume --write
```

Acceptance checklist:

- Volume plan has arcs, turning points, promises, and chapter ranges.
- Output can be validated as structured data.
- The plan cites memory items used for continuity.
- Invalid model output is rejected or repaired with logs.

Stop condition:

- Stop when high-level novel structure is machine-checkable.

## Day 41: 2026-08-05, Chapter Roadmap Generator

Primary objective: turn arcs into chapter-by-chapter roadmap.

Context to read:

- Volume plan from Day 40.
- `daily/02-first-42-days.md`

Work blocks:

- Morning: define chapter roadmap schema: chapter number, title draft, POV, scene list, conflict, hook, reveal, memory dependencies, and acceptance gate.
- Midday: implement roadmap generator.
- Afternoon: add tests for chapter count, missing hooks, unresolved promise handling, and memory dependency references.
- Closeout: generate roadmap for first 12 chapters.

Expected outputs:

- Chapter roadmap generator.
- Roadmap validation tests.
- First roadmap artifact.

Verification:

```powershell
python -m pytest -q tests
pf-agent phase-plan --project demo --level chapter --chapters 12 --write
```

Acceptance checklist:

- Each chapter has a reason to exist.
- Hooks and reveals are explicit.
- Dependencies on memory and earlier chapters are listed.
- Roadmap can be used by chapter workflow without extra interpretation.

Stop condition:

- Stop when the agent can tell tomorrow's writing step from the plan.

## Day 42: 2026-08-06, Editorial Gate Definitions

Primary objective: define professional review gates for planning and drafting.

Context to read:

- `phases/01-phase-acceptance-gates.md`
- Memory audit categories.

Work blocks:

- Morning: define gates: premise clarity, market fit, arc logic, chapter purpose, canon continuity, character motivation, pacing, prose quality, hook strength, and promise tracking.
- Midday: implement gate schema and validation.
- Afternoon: add tests for gate pass, fail, warning, and reviewer override.
- Closeout: attach gates to volume plan and chapter roadmap.

Expected outputs:

- Editorial gate schema.
- Gate validation tests.
- Gate report template.

Verification:

```powershell
python -m pytest -q tests
pf-agent gate list --project demo
```

Acceptance checklist:

- Gates are explicit and reusable.
- Warnings and failures are distinct.
- Human override is auditable.
- Gate results can feed daily recommendations.

Stop condition:

- Stop when planning quality can be reviewed consistently.

## Day 43: 2026-08-07, Daily Workbook Generator Core

Primary objective: generate daily workbooks from plan, memory, and project state.

Context to read:

- `tasks/11-daily-workbook-engine.md`
- `daily/01-daily-workbook-system.md`
- Master calendar contract.

Work blocks:

- Morning: implement daily workbook schema with date, phase, objective, context, tasks, commands, review gates, acceptance checklist, and closeout.
- Midday: implement generator for a single date using project state and chapter roadmap.
- Afternoon: add tests for date selection, missing plan, overdue task, blocked task, and completed previous day.
- Closeout: generate workbook for 2026-08-08.

Expected outputs:

- Daily workbook generator.
- Workbook schema tests.
- Demo daily workbook.

Verification:

```powershell
python -m pytest -q tests
pf-agent daily-workbook --project demo --date 2026-08-08 --write
```

Acceptance checklist:

- The workbook says exactly what to read, write, verify, and close out.
- It references memory and roadmap artifacts.
- It changes recommendations when yesterday was incomplete.
- It is useful without opening the full plan.

Stop condition:

- Stop when a writer can start the day from one generated file.

## Day 44: 2026-08-08, Daily Recommendation Logic

Primary objective: recommend what to do each day based on progress and risk.

Context to read:

- Workbook generator.
- Workflow state architecture.

Work blocks:

- Morning: define recommendation inputs: calendar date, last completed task, open gates, memory audit findings, chapter status, provider availability, and author cadence.
- Midday: implement recommender that chooses writing, planning, review, rewrite, memory cleanup, or rest-buffer work.
- Afternoon: add tests for on-track, behind schedule, blocked by memory contradiction, blocked by provider failure, and ahead-of-plan cases.
- Closeout: generate three recommendation examples.

Expected outputs:

- Daily recommender.
- Recommendation tests.
- Example recommendations.

Verification:

```powershell
python -m pytest -q tests
pf-agent daily-recommend --project demo --date 2026-08-08
```

Acceptance checklist:

- Recommendations are state-based, not a static calendar copy.
- The reason for each recommendation is visible.
- The recommender can choose non-writing maintenance work when quality is at risk.
- The next action is always concrete.

Stop condition:

- Stop when the system can answer "today I should do what, and why?"

## Day 45: 2026-08-09, Weekly Planning Workbook

Primary objective: generate a weekly plan that coordinates chapters, reviews, and memory maintenance.

Context to read:

- Daily workbook system.
- Chapter roadmap.

Work blocks:

- Morning: define weekly workbook sections: target chapters, review days, memory audit window, provider certification check, risks, and fallback plan.
- Midday: implement weekly workbook generation.
- Afternoon: add tests for week boundaries, timezone, skipped days, and catch-up planning.
- Closeout: generate week workbook for 2026-08-10 to 2026-08-16.

Expected outputs:

- Weekly workbook generator.
- Weekly tests.
- Demo weekly workbook.

Verification:

```powershell
python -m pytest -q tests
pf-agent weekly-workbook --project demo --start 2026-08-10 --write
```

Acceptance checklist:

- Weekly plan aligns daily work with chapter roadmap.
- Catch-up logic is explicit.
- Review and memory work are scheduled, not forgotten.
- The output can be used as a professional production sheet.

Stop condition:

- Stop when daily work has weekly context.

## Day 46: 2026-08-10, Monthly Phase Plan

Primary objective: generate monthly or phase-level production plan for longer books.

Context to read:

- Phase roadmap files.
- Weekly workbook output.

Work blocks:

- Morning: define phase-plan fields: objectives, chapter targets, milestone gates, provider checks, memory audits, deliverables, and acceptance standards.
- Midday: implement monthly plan command.
- Afternoon: add tests for month crossing, project delay, arc change, and release target change.
- Closeout: generate September-style monthly plan from demo state.

Expected outputs:

- Monthly phase planner.
- Tests.
- Demo phase plan.

Verification:

```powershell
python -m pytest -q tests
pf-agent phase-plan --project demo --month 2026-09 --write
```

Acceptance checklist:

- The plan is date-specific.
- It includes technical and creative maintenance.
- It updates when progress changes.
- It includes acceptance gates for each milestone.

Stop condition:

- Stop when long projects have a planning rhythm.

## Day 47: 2026-08-11, Plan Change Management

Primary objective: handle outline changes without breaking memory or schedules.

Context to read:

- Memory supersede rules.
- Editorial gate definitions.

Work blocks:

- Morning: define plan-change request schema with reason, affected arcs, affected chapters, affected memory, and approval state.
- Midday: implement change proposal command and impact report.
- Afternoon: add tests for changed chapter order, removed character, merged arc, and delayed reveal.
- Closeout: generate one sample change proposal and impact report.

Expected outputs:

- Plan change workflow.
- Impact report.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent plan change --project demo --dry-run
```

Acceptance checklist:

- Plan changes list affected memory and future chapters.
- Approved changes create auditable state updates.
- Rejected changes do not mutate the roadmap.
- Daily recommendations respond to approved changes.

Stop condition:

- Stop when the system can evolve with the novel.

## Day 48: 2026-08-12, Planning Reports

Primary objective: render planning artifacts for human review.

Context to read:

- Reports architecture.
- Phase plan and daily workbook outputs.

Work blocks:

- Morning: define report formats: Markdown summary, JSON machine output, and concise terminal table.
- Midday: implement report rendering for intake, market analysis, volume plan, chapter roadmap, gates, daily workbook, and weekly workbook.
- Afternoon: add snapshot tests for report structure.
- Closeout: generate a full planning report pack.

Expected outputs:

- Planning report renderer.
- Snapshot tests.
- Report pack.

Verification:

```powershell
python -m pytest -q tests
pf-agent report planning --project demo --write
```

Acceptance checklist:

- Reports are readable without database access.
- Machine-readable outputs remain stable.
- Report filenames include date and project slug.
- Reports include acceptance status, not just content.

Stop condition:

- Stop when planning artifacts can be shared with a writer or editor.

## Day 49: 2026-08-13, Planning UX Polish

Primary objective: make planning commands pleasant and hard to misuse.

Context to read:

- CLI command list.
- Planning reports.

Work blocks:

- Morning: review command names, help text, defaults, error messages, and examples.
- Midday: write CLI recovery messages for missing project state, missing memory index, stale provider certification, and invalid date.
- Afternoon: add tests for CLI help and common operator mistakes.
- Closeout: run planning commands in a clean demo workspace.

Expected outputs:

- Improved help text.
- CLI error tests.
- Demo run notes.

Verification:

```powershell
python -m pytest -q tests
pf-agent phase-plan --help
pf-agent daily-workbook --help
```

Acceptance checklist:

- Help text names required inputs and outputs.
- Errors give next-step recovery.
- Common mistakes are covered by tests.
- Planning commands are discoverable from `pf-agent --help`.

Stop condition:

- Stop when planning can be operated without reading source code.

## Day 50: 2026-08-14, Phase 04 Integration Gate

Primary objective: prove professional planning and daily workbooks are ready for chapter production.

Context to read:

- All Phase 04 files.
- Planning report pack.

Work blocks:

- Morning: run full tests and generate intake, market, volume, chapter roadmap, weekly workbook, and daily workbook.
- Midday: inspect whether every output has acceptance criteria and source context.
- Afternoon: fix planning consistency issues.
- Closeout: write Phase 04 closeout report and Phase 05 start context.

Expected outputs:

- Passing planning tests.
- Planning report pack.
- Phase 04 closeout report.

Verification:

```powershell
python -m pytest -q
pf-agent project intake --project demo --print-template
pf-agent phase-plan --project demo --level chapter --chapters 12 --write
pf-agent daily-workbook --project demo --date 2026-08-15 --write
```

Acceptance checklist:

- The agent can generate stage plans.
- The agent can recommend daily work by date and state.
- Planning uses memory and provider routing.
- Planning outputs include concrete acceptance standards.
- Chapter workflow can start from generated plans.

Stop condition:

- Stop when the plan is operational enough to guide daily writing.
