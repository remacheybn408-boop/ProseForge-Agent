# Task 11: Daily Workbook Engine

## Goal

Generate date-based daily and weekly workbooks from plan, project state, and memory risk.

## Architecture Notes

The workbook is the writer's daily operating document.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/daily/workbook.py`
- Create `src/proseforge_agent/daily/recommend.py`
- Create `tests/test_daily_workbook.py`
- Create `tests/test_daily_recommendations.py`

## Interfaces / Contracts

`DailyWorkbook` contains date, objective, reading context, build block, verification block, integration block, closeout, files, commands, human review questions, acceptance checklist, memory updates, next-day risk.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_daily_workbook.py::test_daily_workbook_recommends_next_state_based_action`**

```python
def test_daily_workbook_recommends_next_state_based_action(project_state):
    workbook = DailyWorkbookEngine().generate(project_state, date="2026-08-15")
    assert workbook.date == "2026-08-15"
    assert workbook.recommendation.next_action
    assert workbook.acceptance_checklist
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_daily_workbook.py::test_daily_workbook_recommends_next_state_based_action -q
```

Expected: FAIL because daily workbook engine is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement workbook dataclasses, state-based recommender, overdue handling, blocked handling, weekly rollup, Markdown/JSON output, and closeout status update.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_daily_workbook.py::test_daily_workbook_recommends_next_state_based_action -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_daily_workbook.py tests/test_daily_recommendations.py -q
pf-agent daily-workbook --project demo --date 2026-08-15 --write
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/daily/workbook.py tests
git commit -m "feat: add daily workbook engine"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_daily_workbook.py tests/test_daily_recommendations.py -q
pf-agent daily-workbook --project demo --date 2026-08-15 --write
```

## Acceptance

- Recommendations are based on state, not only static dates.
- Incomplete work carries forward.
- Memory audit and provider failures can change the recommendation.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
