# Task 73: Sub-Agent Delegation

## Goal

Let the agent delegate a scoped sub-task to a sub-agent that runs with isolated context and restricted permissions, then aggregate the result.

## Agent Product Requirement

A complete agent splits large work into focused sub-agents (research, draft, review) without letting a sub-task see or escalate beyond its scope.

> Dependency note: execute after the autonomous loop (Task 68), planner (Task 69), and permission policy (Task 33).

## Architecture Notes

`SubAgentRunner` runs a sub-task on its own `AgentLoop` (Task 68) with a scoped permission ceiling and an isolated working context, then returns a structured result the parent loop aggregates. A sub-agent's permission ceiling is clamped to at most the parent's grant — it can never escalate. A sub-agent failure is isolated: it returns a failed result, it does not corrupt the parent's context or state. Sub-agents may run in parallel when independent. This is the delegation node in `architecture/11-autonomous-agent-runtime.md`.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Runtime Layers)
- ../architecture/02-system-architecture.md (Dependency Direction)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/subagent.py`
- Create `tests/test_sub_agent.py`
- Create `tests/fixtures/sub-agent-delegation/delegation.json`

## Interfaces / Contracts

- `SubAgentRunner(loop_factory).delegate(task: str, scope: Scope) -> SubAgentResult`.
- `Scope` fields: `permission_ceiling`, `allowed_tools`, `budget`; the ceiling is clamped to <= the parent's ceiling.
- `SubAgentResult` fields: `status`, `output`, `events`, `used_budget`; a failure is contained, never raised into the parent.
- `delegate_many(tasks) -> list[SubAgentResult]` runs independent sub-agents and aggregates results.

## Data Flow

1. Receive a sub-task and its scope.
2. Clamp the scope's permission ceiling to the parent's grant.
3. Run the sub-task on an isolated `AgentLoop` with restricted tools.
4. Capture the result and events.
5. Return a `SubAgentResult` to the parent for aggregation.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_sub_agent.py::test_delegated_subagent_runs_with_scoped_permissions_and_returns_result`**

```python
def test_delegated_subagent_runs_with_scoped_permissions_and_returns_result(fake_loop_factory):
    runner = SubAgentRunner(loop_factory=fake_loop_factory, parent_ceiling="draft_write")
    result = runner.delegate(task="research the setting", scope=Scope(permission_ceiling="system_write"))
    assert result.status in {"completed", "stopped_budget"}
    assert result.effective_ceiling == "draft_write"  # clamped to parent, not escalated
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_sub_agent.py::test_delegated_subagent_runs_with_scoped_permissions_and_returns_result -q
```

Expected: FAIL because `SubAgentRunner`, `Scope`, and `SubAgentResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `SubAgentRunner`, `Scope`, `SubAgentResult`, ceiling clamping, isolated runs, and aggregation.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_sub_agent.py::test_delegated_subagent_runs_with_scoped_permissions_and_returns_result -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_subagent_ceiling_is_clamped_to_parent_grant
test_subagent_failure_does_not_corrupt_parent_context
test_independent_subagents_can_run_in_parallel
test_subagent_results_are_aggregated_for_the_parent
test_subagent_output_round_trips_utf8
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_sub_agent.py -q
pf-agent run --goal "research then draft" --provider fake --delegate
```

Expected: tests pass and the parent run delegates a scoped sub-agent and aggregates its result.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/subagent.py tests/test_sub_agent.py tests/fixtures/sub-agent-delegation
git commit -m "feat: add sub-agent delegation"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Sub-agent results are UTF-8 with relative paths.
- Parallel delegation uses the shared lock (Task 65) for any shared writes.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A sub-agent cannot escalate above the parent's ceiling.
- A sub-agent failure is isolated from the parent.
- Independent sub-agents run in parallel without clobbering shared state.
- Results aggregate back to the parent.

## Verification

```powershell
python -m pytest tests/test_sub_agent.py -q
pf-agent run --goal "research then draft" --provider fake --delegate
```

## Acceptance

- Sub-tasks run on isolated, scoped sub-agents.
- Permission ceilings are clamped, never escalated.
- Sub-agent failures are contained.
- Results are aggregated for the parent.

## Commit Boundary

Commit only sub-agent files and tests after verification passes. Do not change the parent loop's stop conditions here.
