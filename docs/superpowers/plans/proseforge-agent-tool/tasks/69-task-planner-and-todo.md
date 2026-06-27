# Task 69: Task Planner And TODO Tracking

## Goal

Let the agent decompose a goal into ordered sub-tasks and track their status as the autonomous loop works through them.

## Agent Product Requirement

A complete agent breaks a goal into steps it can track and report, instead of treating every request as one opaque action.

> Dependency note: execute after the Agent Kernel (Task 31); consumed by the autonomous loop (Task 68).

## Architecture Notes

`TaskPlanner` produces a `TaskList` of tracked sub-tasks from a goal and context; the autonomous loop (Task 68) selects the next task and writes status back. The plan is data, not execution — the planner runs no tools and calls no provider except through an injected planning hook (so tests are deterministic with the fake). A blocked sub-task is recorded as `blocked`, never silently skipped. The plan can be revised mid-run when new information arrives (ties to steering, Task 74).

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Control Flow)
- ../architecture/02-system-architecture.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/planner.py`
- Create `tests/test_task_planner.py`
- Create `tests/fixtures/task-planner-and-todo/plan_example.json`

## Interfaces / Contracts

- `TaskPlanner(planner_hook=None).decompose(goal: str, context: dict | None = None) -> TaskList`.
- `TaskItem` fields: `id`, `title`, `status` (`pending` | `in_progress` | `done` | `blocked`), `depends_on`, `result_ref`.
- `TaskList.next() -> TaskItem | None` returns the next runnable (`pending`, dependencies done) task.
- `TaskList.update(id, status, ...)` transitions a task; `blocked` requires a reason and never silently drops the task.

## Data Flow

1. Receive the goal and context.
2. Decompose into ordered sub-tasks with dependencies.
3. Expose the next runnable task to the loop.
4. Record status transitions as the loop reports results.
5. Allow mid-run revision when steered or when a task blocks.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_task_planner.py::test_decompose_produces_ordered_subtasks_with_status`**

```python
def test_decompose_produces_ordered_subtasks_with_status():
    plan = TaskPlanner().decompose(goal="写一章：审讯堂发现血玉线索")
    assert len(plan.items) >= 2
    assert all(item.status == "pending" for item in plan.items)
    assert plan.next().id == plan.items[0].id
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_task_planner.py::test_decompose_produces_ordered_subtasks_with_status -q
```

Expected: FAIL because `TaskPlanner`, `TaskList`, and `TaskItem` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `TaskPlanner`, `TaskList`, `TaskItem`, decomposition, `next()`, and status transitions.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_task_planner.py::test_decompose_produces_ordered_subtasks_with_status -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_completed_task_is_marked_done_and_unblocks_dependents
test_blocked_task_records_reason_and_is_not_silently_skipped
test_plan_can_be_revised_mid_run
test_next_returns_none_when_all_tasks_are_done
test_chinese_subtask_titles_round_trip_utf8
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_task_planner.py -q
pf-agent run --goal "写一章开头" --provider fake --show-plan
```

Expected: tests pass and the run prints the decomposed plan with per-task status.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/planner.py tests/test_task_planner.py tests/fixtures/task-planner-and-todo
git commit -m "feat: add task planner and todo tracking"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Plan records are UTF-8 JSON with no platform-specific paths.
- Sub-task titles round-trip Chinese text.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A completed task unblocks its dependents.
- A blocked task carries a reason and stays visible.
- `next()` returns `None` only when every task is done or blocked.
- Mid-run revision does not corrupt existing task status.

## Verification

```powershell
python -m pytest tests/test_task_planner.py -q
pf-agent run --goal "写一章开头" --provider fake --show-plan
```

## Acceptance

- A goal decomposes into ordered, dependency-aware sub-tasks.
- Status transitions are tracked and reportable.
- Blocked tasks are explicit, not dropped.
- Plans are revisable mid-run.

## Commit Boundary

Commit only planner files and tests after verification passes. Do not add execution logic here.
