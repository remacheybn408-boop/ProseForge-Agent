# Task 60: Complete Agent Release Gate

## Goal

Block release until writing workflows, chat, install, provider adaptation, memory, and native OS checks all pass.

## Agent Product Requirement

The final product must ship as a complete agent, not just a novel workflow prototype.

## Architecture Notes

`CompleteAgentReleaseGate` is an aggregator: it consumes the reports other cards already produce and returns a single pass/fail with the list of missing or failing gates. It runs no feature logic itself. It lives in a new `release/` subpackage (record it in architecture 02). Inputs include the E2E fake-provider demo (Task 17), chat drill (Task 31/35), provider shape certification (Task 30), memory audit (Task 08), install doctor (Task 42), native QA matrix (Task 59), docs examples, and the support bundle check (Task 58). A release is blocked if any required gate is absent or failing.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/08-agent-runtime-and-chat.md
- ../architecture/09-installation-and-native-platforms.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/release/__init__.py`
- Create `src/proseforge_agent/release/complete_agent_gate.py`
- Create `tests/test_complete_agent_release_gate.py`
- Create `tests/fixtures/complete-agent-release-gate/reports/`

## Interfaces / Contracts

- `CompleteAgentReleaseGate().evaluate(reports: dict) -> ReleaseDecision`.
- `ReleaseDecision` fields: `passed` (bool), `missing_gates`, `failing_gates`, `summary`.
- Required gates: `e2e_demo`, `chat_drill`, `provider_certification`, `memory_audit`, `install_doctor`, `native_qa`, `docs_examples`, `support_bundle`.
- `passed` is `True` only when every required gate is present and passing; a missing gate counts as a block.

## Data Flow

1. Receive the collected sub-reports.
2. Check each required gate is present.
3. Check each present gate is passing.
4. Aggregate missing and failing gates.
5. Return a single `ReleaseDecision`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_complete_agent_release_gate.py::test_release_blocked_when_chat_and_native_qa_missing`**

```python
def test_release_blocked_when_chat_and_native_qa_missing():
    reports = {"e2e_demo": "pass", "provider_certification": "pass"}  # chat_drill + native_qa absent
    decision = CompleteAgentReleaseGate().evaluate(reports=reports)
    assert decision.passed is False
    assert "chat_drill" in decision.missing_gates
    assert "native_qa" in decision.missing_gates
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_complete_agent_release_gate.py::test_release_blocked_when_chat_and_native_qa_missing -q
```

Expected: FAIL because `CompleteAgentReleaseGate` and `ReleaseDecision` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `CompleteAgentReleaseGate`, `ReleaseDecision`, gate presence/pass checks, and aggregation.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_complete_agent_release_gate.py::test_release_blocked_when_chat_and_native_qa_missing -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_release_passes_when_all_required_gates_pass
test_failing_gate_blocks_release_and_is_listed
test_missing_gate_is_treated_as_a_block
test_decision_summary_lists_all_required_gates
test_report_paths_are_portable
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_complete_agent_release_gate.py -q
pf-agent release check --complete-agent --write-report
```

Expected: tests pass and the release check prints a pass/fail decision listing missing and failing gates.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_complete_agent_release_gate.py -q
```

Expected: PASS; the gate aggregates report data and is platform-agnostic.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/release tests/test_complete_agent_release_gate.py tests/fixtures/complete-agent-release-gate
git commit -m "feat: add complete agent release gate"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The gate consumes report data; it runs on any host.
- Report paths are relative, never absolute machine paths.
- Aggregated summaries are UTF-8.

## Failure Modes To Prove

- A missing required gate blocks the release.
- A failing gate is listed and blocks the release.
- Release passes only when every gate is present and passing.
- The gate runs no feature logic of its own.

## Verification

```powershell
python -m pytest tests/test_complete_agent_release_gate.py -q
pf-agent release check --complete-agent --write-report
```

## Acceptance

- Release is blocked unless all required gates pass.
- Missing and failing gates are reported explicitly.
- The gate is a pure aggregator over existing reports.
- It lives in the `release/` subpackage recorded in architecture 02.

## Commit Boundary

Commit only release-gate files and tests after verification passes. Do not implement the underlying gates here.
