# Task 74: Interruptibility And Steering

## Goal

Let the user interrupt or redirect a running autonomous task at a safe point without losing progress.

## Agent Product Requirement

A complete agent can be stopped or steered mid-task — the user is always in control of a long-running run.

> Dependency note: execute after the autonomous loop (Task 68) and planner (Task 69).

## Architecture Notes

`control` provides a cooperative cancellation/steering token the autonomous loop (Task 68) checks at each safe point (between iterations, never mid-write). An interrupt stops the run cleanly with `interrupted` status and a saved, resumable state. A steer injects a new instruction that the planner (Task 69) merges into the current plan rather than discarding progress. Control is cooperative (no forced thread kill) so state is never left half-written. Every interrupt/steer is recorded as an event (Task 40).

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Budgets And Safety Guardrails)
- ../architecture/02-system-architecture.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/control.py`
- Create `tests/test_control_interrupt.py`
- Create `tests/fixtures/interruptibility-and-steering/signals.json`

## Interfaces / Contracts

- `ControlToken()` exposes `interrupt()`, `steer(instruction)`, and `poll() -> ControlSignal | None`.
- The loop calls `poll()` only at safe points; an `interrupt` signal stops with `status="interrupted"` and a resumable checkpoint.
- A `steer` signal returns a new instruction the planner merges into the plan; existing completed work is preserved.
- Interrupt leaves persisted state consistent (saved after the last completed step), enabling resume.

## Data Flow

1. The user (or UI/API) sets an interrupt or steer signal on the token.
2. The loop polls the token at the next safe point.
3. Interrupt → save checkpoint, stop with `interrupted`.
4. Steer → merge the new instruction into the plan, continue.
5. Emit a control event either way.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_control_interrupt.py::test_interrupt_signal_stops_loop_at_next_safe_point`**

```python
def test_interrupt_signal_stops_loop_at_next_safe_point(fake_kernel_runs_forever):
    token = ControlToken()
    loop = AgentLoop(kernel=fake_kernel_runs_forever, budget=Budget(max_iterations=100), control=token)
    token.interrupt()  # request stop before/while running
    result = loop.run(goal="loop a while")
    assert result.status == "interrupted"
    assert result.resumable is True
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_control_interrupt.py::test_interrupt_signal_stops_loop_at_next_safe_point -q
```

Expected: FAIL because `ControlToken` and `ControlSignal` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ControlToken`, `ControlSignal`, safe-point polling, interrupt checkpointing, and steer merging.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_control_interrupt.py::test_interrupt_signal_stops_loop_at_next_safe_point -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_interrupt_saves_resumable_state_without_data_loss
test_steer_merges_new_instruction_into_plan
test_interrupted_run_can_be_resumed
test_control_signals_are_emitted_as_events
test_interrupt_only_takes_effect_at_a_safe_point
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_control_interrupt.py -q
pf-agent run --goal "draft three openings" --provider fake & pf-agent run --interrupt
```

Expected: tests pass and an interrupt stops the run cleanly with a resumable checkpoint.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/control.py tests/test_control_interrupt.py tests/fixtures/interruptibility-and-steering
git commit -m "feat: add interruptibility and steering"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Cooperative cancellation works without OS-specific signals.
- Checkpoints are UTF-8 with relative paths.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- Interrupt takes effect only at a safe point, never mid-write.
- An interrupted run saves resumable state with no data loss.
- A steer merges into the plan without discarding completed work.
- An interrupted run can be resumed.

## Verification

```powershell
python -m pytest tests/test_control_interrupt.py -q
```

## Acceptance

- A running task can be interrupted at a safe point.
- A running task can be steered with a new instruction.
- Interrupted runs are resumable with consistent state.
- Control actions are traced.

## Commit Boundary

Commit only control files and tests after verification passes. Do not use forced thread termination.
