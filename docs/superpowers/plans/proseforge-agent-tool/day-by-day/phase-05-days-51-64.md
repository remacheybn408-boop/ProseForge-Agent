# Phase 05: Chapter Production Workflow

Dates: 2026-08-15 to 2026-08-28.

Goal: make one chapter move through prepare, draft, review, rewrite, accept, memory update, ProseForge export, and daily closeout.

## Day 51: 2026-08-15, Workflow State Machine

Primary objective: implement durable workflow state and recovery.

Context to read:

- `tasks/12-workflow-state-and-recovery.md`
- `architecture/06-workflow-engine.md`

Work blocks:

- Morning: define workflow states: created, context_ready, drafted, reviewed, needs_revision, revised, accepted, exported, memory_updated, failed, and paused.
- Midday: implement state persistence with step id, inputs, outputs, artifacts, provider used, retry count, and timestamps.
- Afternoon: add tests for transition validity, interrupted step recovery, failed step retry, and invalid manual transition.
- Closeout: add `pf-agent workflow status`.

Expected outputs:

- Workflow state machine.
- Recovery tests.
- Status command.

Verification:

```powershell
python -m pytest -q tests
pf-agent workflow status --project demo
```

Acceptance checklist:

- Workflow steps are resumable.
- State files are human-inspectable.
- Invalid transitions are rejected.
- Provider and artifact history are preserved.

Stop condition:

- Stop when chapter work can survive interruption.

## Day 52: 2026-08-16, Chapter Context Preparation

Primary objective: prepare a chapter package before drafting.

Context to read:

- `tasks/13-chapter-lifecycle-workflow.md`
- Evidence pack builder.
- Chapter roadmap.

Work blocks:

- Morning: define chapter context package: roadmap entry, active memory, previous chapter summary, target word count, scene beats, constraints, and acceptance gates.
- Midday: implement context preparation command.
- Afternoon: add tests for missing roadmap, stale memory audit, unresolved contradiction, and normal context package.
- Closeout: generate context for demo chapter 1.

Expected outputs:

- Chapter context package builder.
- Tests.
- Demo context package.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter prepare --project demo --chapter 1 --write
```

Acceptance checklist:

- The drafter receives all necessary constraints before writing.
- Context package cites evidence sources.
- Blocked quality risks stop drafting with a clear reason.
- Package can be regenerated deterministically from same state.

Stop condition:

- Stop when drafting has a professional brief.

## Day 53: 2026-08-17, Chapter Draft Prompt And Output Contract

Primary objective: define how the agent asks a model to draft a chapter.

Context to read:

- Chapter context package.
- Provider routing policy.

Work blocks:

- Morning: write draft prompt contract with role, audience, style, scene beats, hard constraints, forbidden contradictions, target length, and output format.
- Midday: implement draft output contract with manuscript text, scene summaries, self-check, used evidence, and open questions.
- Afternoon: add fake provider tests for valid draft, too-short draft, missing evidence references, and malformed output.
- Closeout: run one fake draft.

Expected outputs:

- Draft prompt builder.
- Draft output validator.
- Tests and fake draft artifact.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter draft --project demo --chapter 1 --provider fake --write
```

Acceptance checklist:

- Draft prompts separate canon from suggestions.
- Draft output has manuscript text plus structured metadata.
- Invalid draft output is rejected before review.
- The chosen provider role is recorded.

Stop condition:

- Stop when chapter drafting has a stable contract.

## Day 54: 2026-08-18, First Draft Workflow

Primary objective: run prepare and draft as a single workflow.

Context to read:

- Workflow state machine.
- Draft prompt and output contract.

Work blocks:

- Morning: implement `chapter run --until draft`.
- Midday: connect state transitions, context artifacts, provider router, fake provider, and draft validator.
- Afternoon: add tests for successful draft, provider retry, provider failure, and resume after interrupted draft.
- Closeout: generate one demo draft through the workflow command.

Expected outputs:

- Draft workflow command.
- Integration tests.
- Demo draft artifact.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter run --project demo --chapter 1 --until draft --provider fake
```

Acceptance checklist:

- One command can prepare and draft a chapter.
- Workflow state records every artifact path.
- Failures can resume without duplicating accepted artifacts.
- The fake provider path is fully deterministic.

Stop condition:

- Stop when the first half of chapter production is automated.

## Day 55: 2026-08-19, Editorial Review Workflow

Primary objective: review a draft against professional gates.

Context to read:

- `tasks/14-rewrite-and-accept-workflow.md`
- Editorial gate definitions.

Work blocks:

- Morning: define review categories: continuity, plot logic, character motivation, pacing, prose quality, hook strength, promise handling, market fit, and risk flags.
- Midday: implement reviewer prompt and review report parser.
- Afternoon: add tests for pass, fail, warning, contradiction detection, and review-output repair.
- Closeout: run fake review on demo draft.

Expected outputs:

- Review workflow.
- Review report schema.
- Tests.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter review --project demo --chapter 1 --provider fake --write
```

Acceptance checklist:

- Reviews cite chapter lines or sections where possible.
- Gate failures are actionable.
- Review output separates objective continuity errors from taste suggestions.
- Review status can move workflow to accepted or needs_revision.

Stop condition:

- Stop when draft quality can be evaluated consistently.

## Day 56: 2026-08-20, Rewrite Planning

Primary objective: create targeted rewrite plans from review findings.

Context to read:

- Review report.
- Memory evidence pack.

Work blocks:

- Morning: define rewrite plan schema: issue id, priority, affected scene, proposed change, memory references, risk, and acceptance criteria.
- Midday: implement rewrite planner using reviser role.
- Afternoon: add tests for continuity fix, pacing fix, prose polish, rejected review item, and conflicting suggestions.
- Closeout: create rewrite plan for demo chapter.

Expected outputs:

- Rewrite plan generator.
- Rewrite plan tests.
- Demo rewrite plan.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter rewrite-plan --project demo --chapter 1 --write
```

Acceptance checklist:

- Rewrite plans are targeted and not full regeneration by default.
- High-priority continuity fixes outrank prose polish.
- Every rewrite item has acceptance criteria.
- Rejected or deferred suggestions are recorded.

Stop condition:

- Stop when rewriting has a plan, not a vague instruction.

## Day 57: 2026-08-21, Rewrite Execution

Primary objective: apply rewrite plans through the provider adapter and validate revised output.

Context to read:

- Rewrite plan.
- Draft output contract.

Work blocks:

- Morning: implement rewrite prompt builder that includes selected draft sections, evidence, and exact rewrite items.
- Midday: implement revised draft validator and change summary.
- Afternoon: add tests for full chapter rewrite, scene rewrite, minimal polish, rejected malformed revision, and provider failure.
- Closeout: run fake rewrite on demo chapter.

Expected outputs:

- Rewrite executor.
- Revised draft validator.
- Change summary report.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter rewrite --project demo --chapter 1 --provider fake --write
```

Acceptance checklist:

- Rewrites preserve unchanged sections unless the plan says otherwise.
- Revised output includes change summary and evidence references.
- Failed revision does not overwrite previous accepted artifact.
- Review status can loop back for another review.

Stop condition:

- Stop when revision is controlled and auditable.

## Day 58: 2026-08-22, Accept And Lock Chapter

Primary objective: accept a chapter and lock it as project state.

Context to read:

- ProseForge action bridge.
- Memory update rules.

Work blocks:

- Morning: define acceptance package: final text, review result, gate status, memory update candidates, export readiness, and human approval state.
- Midday: implement `chapter accept` with optional human approval flag and audit record.
- Afternoon: add tests for accept passed chapter, reject failed gates, force accept with audit reason, and duplicate acceptance.
- Closeout: accept demo chapter with fake artifacts.

Expected outputs:

- Chapter acceptance command.
- Audit tests.
- Accepted chapter artifact.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter accept --project demo --chapter 1 --reason "demo acceptance"
```

Acceptance checklist:

- Failed gates cannot be ignored without an audit reason.
- Accepted text is immutable unless superseded by a new accepted version.
- Acceptance triggers memory update candidates.
- Workflow state records accepted artifact id.

Stop condition:

- Stop when chapter output has a real editorial gate.

## Day 59: 2026-08-23, Export To ProseForge

Primary objective: hand accepted chapters back to ProseForge for reports and export.

Context to read:

- `tasks/03-proseforge-engine-adapter.md`
- Accepted chapter artifact.

Work blocks:

- Morning: map accepted chapter fields to ProseForge slot or manuscript layout.
- Midday: implement export bridge with dry-run and write modes.
- Afternoon: add tests for path mapping, dry-run, existing chapter conflict, and export failure.
- Closeout: run dry-run export against local ProseForge path.

Expected outputs:

- ProseForge export bridge.
- Export tests.
- Dry-run export report.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter export --project demo --chapter 1 --to-proseforge --dry-run
```

Acceptance checklist:

- Export never overwrites existing manuscript text without explicit mode.
- Dry-run shows exact target paths.
- ProseForge errors are preserved in the workflow state.
- Export status appears in daily closeout.

Stop condition:

- Stop when accepted work can return to the ProseForge ecosystem.

## Day 60: 2026-08-24, Chapter Memory Update

Primary objective: update memory after acceptance and export.

Context to read:

- Day 35 post-draft memory updater.
- Accepted chapter package.

Work blocks:

- Morning: implement accepted-chapter memory update command.
- Midday: run classification for new canon, character changes, promise updates, timeline events, and style observations.
- Afternoon: add tests for accepted-only update, duplicate prevention, promise resolution, and review queue creation.
- Closeout: generate memory update report for demo chapter.

Expected outputs:

- Accepted chapter memory updater.
- Memory update tests.
- Memory update report.

Verification:

```powershell
python -m pytest -q tests
pf-agent memory update-from-accepted --project demo --chapter 1 --write-candidates
```

Acceptance checklist:

- Only accepted chapters can update canon-sensitive memory.
- Memory candidates preserve chapter source references.
- Promise tracking changes are visible.
- Review queue receives canon changes.

Stop condition:

- Stop when completed writing improves future retrieval.

## Day 61: 2026-08-25, Daily Closeout Automation

Primary objective: close the writing day and recommend tomorrow's work.

Context to read:

- Daily workbook generator.
- Workflow state.

Work blocks:

- Morning: define closeout fields: completed tasks, skipped tasks, artifacts, tests run, gate status, memory changes, risks, and tomorrow recommendation.
- Midday: implement `daily closeout` command that reads workflow state and updates workbook status.
- Afternoon: add tests for completed day, partial day, blocked day, failed provider day, and memory-risk day.
- Closeout: run closeout for demo chapter day.

Expected outputs:

- Daily closeout command.
- Closeout tests.
- Tomorrow recommendation output.

Verification:

```powershell
python -m pytest -q tests
pf-agent daily closeout --project demo --date 2026-08-25 --write
```

Acceptance checklist:

- Closeout is based on real artifacts and workflow state.
- Tomorrow recommendation names the next concrete action.
- Incomplete work is carried forward.
- Memory and provider risks affect tomorrow's plan.

Stop condition:

- Stop when daily work becomes a closed loop.

## Day 62: 2026-08-26, Multi-Chapter Batch Planning

Primary objective: coordinate repeated chapter production over a week.

Context to read:

- Weekly workbook generator.
- Chapter workflow status.

Work blocks:

- Morning: define batch plan fields: chapter queue, dependencies, review windows, provider budget, memory audit windows, and fallback days.
- Midday: implement `chapter queue` and `chapter next` commands.
- Afternoon: add tests for blocked chapter, next-ready chapter, overdue review, and memory-audit interruption.
- Closeout: create queue for chapters 1 to 5.

Expected outputs:

- Chapter queue commands.
- Queue tests.
- Batch plan report.

Verification:

```powershell
python -m pytest -q tests
pf-agent chapter queue --project demo --chapters 1-5 --write
pf-agent chapter next --project demo
```

Acceptance checklist:

- The system can choose the next chapter based on dependencies.
- Review and memory work can block unsafe drafting.
- Queue output is easy to scan.
- Daily workbook can consume queue status.

Stop condition:

- Stop when professional cadence is supported beyond one chapter.

## Day 63: 2026-08-27, Workflow Failure Drills

Primary objective: test chapter workflow under realistic failures.

Context to read:

- Workflow state machine.
- Provider fallback router.

Work blocks:

- Morning: create failure fixtures: provider timeout, malformed model output, memory contradiction, ProseForge export failure, and interrupted process.
- Midday: run failure drills and record expected recovery behavior.
- Afternoon: add automated tests for each failure drill.
- Closeout: update risk register with residual workflow risks.

Expected outputs:

- Failure drill tests.
- Recovery report.
- Risk register updates.

Verification:

```powershell
python -m pytest -q tests
pf-agent workflow drill --project demo --scenario provider_timeout
```

Acceptance checklist:

- Failures do not silently mark work complete.
- Recovery instructions are visible in CLI output.
- Workflow state preserves partial artifacts for debugging.
- Provider fallback does not duplicate accepted chapters.

Stop condition:

- Stop when chapter workflow is resilient enough for daily use.

## Day 64: 2026-08-28, Phase 05 Integration Gate

Primary objective: prove one chapter can move through the whole production loop.

Context to read:

- All Phase 05 files.
- Phase 05 failure drill report.

Work blocks:

- Morning: run prepare, draft, review, rewrite, accept, export dry-run, memory update, and daily closeout with fake provider.
- Midday: inspect all artifacts and state transitions.
- Afternoon: fix integration gaps and update workflow docs.
- Closeout: write Phase 05 closeout report and Phase 06 start context.

Expected outputs:

- Full chapter lifecycle demo.
- Passing workflow tests.
- Phase 05 closeout report.

Verification:

```powershell
python -m pytest -q
pf-agent chapter run --project demo --chapter 1 --provider fake
pf-agent daily closeout --project demo --date 2026-08-28 --write
```

Acceptance checklist:

- One chapter can complete the entire workflow.
- Deep memory is updated through reviewable candidates.
- ProseForge export path is tested in dry-run.
- Daily recommendation advances based on completed work.
- Failure drills have automated coverage.

Stop condition:

- Stop when ProseForge Agent is a working novel-production agent, not only a planner.
