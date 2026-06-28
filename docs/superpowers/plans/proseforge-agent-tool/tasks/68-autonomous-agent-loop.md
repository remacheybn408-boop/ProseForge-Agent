# Task 68: Autonomous Agent Loop

## Goal

Turn the per-turn kernel into a multi-step autonomous loop that plans, acts, observes, verifies, and repeats until the goal is met, the budget is spent, progress stalls, or the user interrupts.

## Agent Product Requirement

A complete agent must pursue a goal across many steps on its own, not just answer one turn — while staying bounded so it never runs away.

> Dependency note: execute after the Agent Kernel (Task 31). It uses the planner (69), reflection (70), control (74), and metering budget (61) as those land.

## Architecture Notes

`AgentLoop` orchestrates many kernel turns; it does not modify the kernel (Task 31), which stays single-turn and independently testable. The loop owns the stop conditions and budgets, manages the run's working context, and compacts that context when it grows past a threshold so long runs stay within the model window. It emits an event per step (Task 40). This module implements the control flow in `architecture/11-autonomous-agent-runtime.md`.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Control Flow, Budgets And Safety Guardrails)
- ../architecture/02-system-architecture.md (Dependency Direction)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/loop.py`
- Create `tests/test_agent_loop.py`
- Create `tests/fixtures/autonomous-agent-loop/run_trace.json`

## Interfaces / Contracts

- `AgentLoop(kernel, budget, planner=None, verifier=None, control=None).run(goal: str, context: dict | None = None) -> LoopResult`.
- `LoopResult` fields: `status` (`completed` | `stopped_budget` | `stopped_no_progress` | `interrupted`), `steps` (list of step records), `final_text`, `transcript_ref`.
- `Budget` carries `max_iterations` and an optional cost cap (delegated to Task 61); the loop never exceeds `max_iterations`.
- The loop calls `kernel.run_turn(...)` once per iteration and stops as soon as a stop condition holds; it does not mutate the kernel.

## Data Flow

1. Build (or receive) a plan for the goal.
2. Each iteration: select next work, call `kernel.run_turn`, capture result and events.
3. Verify the step result; on failure, allow bounded reflection/retry.
4. Compact working context if it exceeds the threshold.
5. Check stop conditions (done / budget / no-progress / interrupt) and either continue or return `LoopResult`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_agent_loop.py::test_loop_stops_when_goal_satisfied_within_budget`**

```python
def test_loop_stops_when_goal_satisfied_within_budget(fake_kernel_done_on_second_turn):
    loop = AgentLoop(kernel=fake_kernel_done_on_second_turn, budget=Budget(max_iterations=10))
    result = loop.run(goal="say hello then stop")
    assert result.status == "completed"
    assert len(result.steps) == 2
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_agent_loop.py::test_loop_stops_when_goal_satisfied_within_budget -q
```

Expected: FAIL because `AgentLoop`, `Budget`, and `LoopResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `AgentLoop`, `Budget`, `LoopResult`, the per-iteration step, stop conditions, and context compaction.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_agent_loop.py::test_loop_stops_when_goal_satisfied_within_budget -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_loop_halts_at_iteration_budget_without_infinite_loop
test_no_progress_is_detected_and_stops_the_run
test_working_context_is_compacted_when_over_threshold
test_each_iteration_emits_an_event_with_trace_id
test_interrupt_signal_stops_with_interrupted_status
test_loop_does_not_mutate_the_kernel
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_agent_loop.py -q
pf-agent run --goal "draft a one-line opening" --provider fake --max-iterations 5
```

Expected: tests pass and the autonomous run completes within the iteration budget, printing its step summary.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/loop.py tests/test_agent_loop.py tests/fixtures/autonomous-agent-loop
git commit -m "feat: add autonomous agent loop"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Step records and transcripts are UTF-8 with relative paths.
- No platform-specific timing assumptions in stop conditions.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- The loop never exceeds `max_iterations` (no infinite loop).
- A stalled run stops with `stopped_no_progress`, not silently spinning.
- An over-threshold working context is compacted, not truncated blindly.
- An interrupt stops the run at a safe point with `interrupted` status.

## Verification

```powershell
python -m pytest tests/test_agent_loop.py -q
pf-agent run --goal "draft a one-line opening" --provider fake --max-iterations 5
```

## Acceptance

- The loop runs multiple kernel turns toward a goal.
- It is bounded by iteration (and cost) budgets and a no-progress detector.
- Working context is compacted on long runs.
- The kernel is reused unmodified.

## Commit Boundary

Commit only the loop files and tests after verification passes. Do not change the kernel here.
