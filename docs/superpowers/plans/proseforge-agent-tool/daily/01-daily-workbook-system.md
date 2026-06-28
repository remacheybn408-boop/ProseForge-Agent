# Daily Workbook System

## Purpose

The daily workbook turns an overwhelming novel project into today's concrete work. It must be date-aware, project-aware, phase-aware, and evidence-aware.

## File Location

Generated files should live under:

```text
workspace/daily_workbooks/<project_slug>/YYYY-MM-DD.md
```

Example:

```text
workspace/daily_workbooks/demo_novel/2026-06-26.md
```

## Required Inputs

- Date.
- Project slug.
- Project title.
- Current phase.
- Current workflow state.
- Active ProseForge slot.
- Current volume and chapter when available.
- Last daily closeout when available.
- Latest evidence pack when available.
- Latest ProseForge report when available.

## Required Sections

### 1. Header

Must include exact date and project title.

```markdown
# Daily Workbook - 2026-06-26 - Demo Novel
```

### 2. Today Focus

Required fields:

- Phase.
- Main target.
- Chapter target.
- Word target.
- Model role.
- ProseForge action.
- Expected artifact.

### 3. Context To Read

This section prevents blind writing. It lists:

- Latest phase plan.
- Latest workflow run.
- Previous daily closeout.
- Relevant ProseForge report.
- Evidence pack path.
- Memory warnings.

### 4. Automatic Retrieval Plan

Required fields:

- Retrieval intent.
- Query string.
- Sources to search.
- Expected memory types.
- Degraded fallback.

### 5. Writing Or Engineering Blocks

The workbook separates the day into blocks:

1. Setup block.
2. Retrieval block.
3. Main work block.
4. Verification block.
5. Memory block.
6. Closeout block.

### 6. Closeout

Required checklist:

- [ ] Target artifact saved.
- [ ] Verification command run or skipped with reason.
- [ ] Memory updates captured.
- [ ] Retrieval log saved.
- [ ] ProseForge action completed or failure recorded.
- [ ] Tomorrow recommendation generated.

## Recommendation Logic

The first release uses deterministic rules:

| State | Recommendation |
| --- | --- |
| No package skeleton | Do Task 01 |
| Config missing | Do Task 02 |
| Engine adapter missing | Do Task 03 |
| Provider layer missing | Do Tasks 04 through 06 |
| Memory missing | Do Tasks 07 and 08 |
| Retrieval missing | Do Task 09 |
| Daily generator missing | Do Task 11 |
| No active ProseForge slot | Run project binding/status |
| Pre exists but no draft | Draft chapter |
| Draft exists but no post | Run `post` |
| Post report has major warnings | Run rewrite workflow |
| Chapter accepted | Generate next daily workbook |

## Daily Workbook Data Model

```json
{
  "date": "2026-06-26",
  "project_slug": "demo_novel",
  "project_title": "Demo Novel",
  "phase_name": "Foundation",
  "main_target": "Create package skeleton",
  "chapter_target": "No chapter drafting today",
  "word_target": 0,
  "model_role": "planner",
  "proseforge_action": "none",
  "expected_artifact": "pyproject.toml and package files",
  "retrieval_intent": {},
  "evidence_pack_path": "",
  "verification_commands": [],
  "tomorrow_recommendation": ""
}
```

## Example Workbook

```markdown
# Daily Workbook - 2026-06-26 - Demo Novel

## Today Focus

- Phase: Foundation
- Main target: Create package skeleton
- Chapter target: No chapter drafting today
- Writing word target: 0
- Primary model role: planner
- Required ProseForge action: none
- Expected artifact: package skeleton and config tests

## Context To Read

- Plan index: docs/superpowers/plans/proseforge-agent-tool/00-index.md
- Task card: docs/superpowers/plans/proseforge-agent-tool/tasks/01-package-skeleton.md
- Existing engine root: $PROSEFORGE_ROOT

## Work Blocks

1. Setup block: create package files.
2. Verification block: run test_config.
3. Memory block: no memory extraction today.
4. Closeout block: record Task 01 status.

## Closeout

- [ ] Target artifact saved.
- [ ] Verification command run or skipped with reason.
- [ ] Memory changes captured.
- [ ] Retrieval log saved.
- [ ] ProseForge action completed or failure recorded.
- [ ] Tomorrow recommendation generated.
```

## Acceptance Criteria

- Can generate a workbook for any date string.
- Workbook includes exact date.
- Workbook includes closeout checklist.
- Workbook can be generated without LLM.
- Workbook can be written to disk.
- Tomorrow recommendation is deterministic from current state.
