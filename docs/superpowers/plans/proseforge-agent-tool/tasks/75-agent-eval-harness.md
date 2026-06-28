# Task 75: Agent Eval And Task-Success Harness

## Goal

Measure the agent's task-success rate over a golden task suite so autonomy quality is a gate, not a guess.

## Agent Product Requirement

A complete agent is judged by whether it completes tasks, not only by unit tests of its parts. That success rate must be measurable and enforced before release.

> Dependency note: execute after the autonomous loop (Task 68) and self-verification (Task 70). Consumed by CI (Task 64) and the release gate (Task 60).

## Architecture Notes

`eval` runs the autonomous loop (Task 68) over a fixed suite of golden tasks, each with deterministic success criteria, using the fake provider so results are reproducible and offline. It reports per-task pass/fail, the aggregate success rate, steps, and budget used. The release gate (Task 60) and CI (Task 64) consume the success rate as an agent-level quality gate. The harness scores; it does not change agent behavior.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Acceptance Criteria)
- ../appendices/02-test-matrix.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/eval.py`
- Create `tests/eval/test_agent_eval.py`
- Create `tests/eval/suite/golden_tasks.json`

## Interfaces / Contracts

- `EvalHarness(loop_factory, suite).run() -> EvalReport`.
- `GoldenTask` fields: `id`, `goal`, `success_criteria`, `max_iterations`.
- `EvalReport` fields: `success_rate`, `results` (per-task pass/fail + steps + used_budget), `threshold`, `passed`.
- `passed` is `True` only when `success_rate >= threshold`; runs are deterministic with the fake provider.

## Data Flow

1. Load the golden task suite.
2. Run each task on a fresh autonomous loop with the fake provider.
3. Score each result against its success criteria (Task 70 verifiers).
4. Aggregate the success rate and compare to the threshold.
5. Return an `EvalReport` (Markdown/JSON renderable).

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/eval/test_agent_eval.py::test_eval_reports_task_success_rate_over_golden_suite`**

```python
def test_eval_reports_task_success_rate_over_golden_suite(fake_loop_factory, golden_suite):
    report = EvalHarness(loop_factory=fake_loop_factory, suite=golden_suite).run()
    assert 0.0 <= report.success_rate <= 1.0
    assert len(report.results) == len(golden_suite.tasks)
    assert isinstance(report.passed, bool)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/eval/test_agent_eval.py::test_eval_reports_task_success_rate_over_golden_suite -q
```

Expected: FAIL because `EvalHarness`, `GoldenTask`, and `EvalReport` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `EvalHarness`, `GoldenTask`, `EvalReport`, suite loading, scoring, and threshold comparison.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/eval/test_agent_eval.py::test_eval_reports_task_success_rate_over_golden_suite -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_success_rate_below_threshold_marks_report_not_passed
test_each_golden_task_has_explicit_success_criteria
test_eval_is_deterministic_across_repeated_runs
test_eval_report_renders_markdown_and_json
test_release_gate_consumes_eval_success_rate
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/eval -q
pf-agent eval run --provider fake --write-report
```

Expected: tests pass and the eval run prints a per-task and aggregate success rate.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/eval.py tests/eval
git commit -m "feat: add agent eval and task-success harness"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The suite and reports are UTF-8 with no machine-specific paths.
- Evaluation is offline and deterministic via the fake provider.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A success rate below threshold marks the report not passed (blocks release).
- Every golden task has explicit success criteria.
- Repeated runs produce identical results (determinism).
- The release gate can consume the success rate.

## Verification

```powershell
python -m pytest tests/eval -q
pf-agent eval run --provider fake --write-report
```

## Acceptance

- Task-success rate is measured over a golden suite.
- The rate is enforced against a threshold and consumed by the release gate.
- Evaluation is deterministic and offline.
- Reports render as Markdown and JSON.

## Commit Boundary

Commit only eval files and the eval suite after verification passes. Do not alter agent behavior to game the suite.
