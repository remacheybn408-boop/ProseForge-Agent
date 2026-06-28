# Task 70: Self-Verification And Reflection

## Goal

Make the agent check its own output against the sub-task's criteria and, on failure, reflect and retry within a bounded budget.

## Agent Product Requirement

A complete agent does not blindly accept its first output; it verifies, and when it falls short it revises — like running tests and fixing failures.

> Dependency note: execute after the Agent Kernel (Task 31) and planner (Task 69); consumed by the autonomous loop (Task 68).

## Architecture Notes

`Verifier` checks a step output against acceptance criteria and returns a structured verdict; on failure `Reflector` produces a revised plan/prompt and the loop retries within the reflection budget. Domain verifiers are pluggable: the ProseForge `post`/`review` gates register as verifiers so a failed writing guard triggers a rewrite instead of a silent accept. Verification itself runs no mutating action; it only judges and proposes. This realises the verify step in `architecture/11-autonomous-agent-runtime.md`.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Control Flow, Writing As The First Vertical)
- ../architecture/02-system-architecture.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/reflection.py`
- Create `tests/test_self_verification.py`
- Create `tests/fixtures/self-verification-and-reflection/criteria.json`

## Interfaces / Contracts

- `Verifier(verifiers).check(output, criteria) -> VerifyResult`; `VerifyResult` fields: `passed`, `failures` (list of `{criterion, detail}`), `score`.
- `Reflector().revise(output, verdict) -> Revision` with a concrete next-attempt instruction.
- `register(name, verifier_fn)` adds a domain verifier (e.g. `proseforge_post`, `proseforge_review`).
- Reflection retries are bounded by a `max_reflections` budget; a passing verdict triggers no retry.

## Data Flow

1. Receive a step output and its acceptance criteria.
2. Run all applicable verifiers (generic + registered domain verifiers).
3. Aggregate a pass/fail verdict with specific failures.
4. On fail (within budget), produce a revision instruction and signal retry.
5. On pass, mark the step verified.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_self_verification.py::test_failed_verification_triggers_one_reflection_retry`**

```python
def test_failed_verification_triggers_one_reflection_retry():
    verifier = Verifier(verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]})
    verdict = verifier.check(output="短", criteria={"min_length": 50})
    assert verdict.passed is False
    revision = Reflector().revise(output="短", verdict=verdict)
    assert revision.retry is True
    assert revision.instruction
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_self_verification.py::test_failed_verification_triggers_one_reflection_retry -q
```

Expected: FAIL because `Verifier`, `VerifyResult`, and `Reflector` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `Verifier`, `VerifyResult`, `Reflector`, `Revision`, verifier registration, and the reflection budget.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_self_verification.py::test_failed_verification_triggers_one_reflection_retry -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_passing_verification_triggers_no_retry
test_reflection_is_bounded_by_max_reflections
test_proseforge_review_can_register_as_a_domain_verifier
test_reflection_reason_is_emitted_as_event
test_verifier_failures_list_each_unmet_criterion
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_self_verification.py -q
pf-agent run --goal "写满 200 字的开头" --provider fake --verify
```

Expected: tests pass and a too-short output triggers one bounded reflection retry before stopping.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/reflection.py tests/test_self_verification.py tests/fixtures/self-verification-and-reflection
git commit -m "feat: add self-verification and reflection"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Criteria and verdicts are UTF-8 data with no platform-specific paths.
- Domain verifiers (ProseForge gates) run through the engine adapter, not a hard-coded path.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- A passing verdict causes no retry.
- Reflection never exceeds `max_reflections` (no infinite revise loop).
- A failed ProseForge review triggers a rewrite, not a silent accept.
- Each unmet criterion is listed in the verdict.

## Verification

```powershell
python -m pytest tests/test_self_verification.py -q
pf-agent run --goal "写满 200 字的开头" --provider fake --verify
```

## Acceptance

- Output is checked against per-sub-task criteria.
- Failures trigger bounded reflection and retry.
- Domain verifiers (ProseForge gates) are pluggable.
- Verification performs no mutating action.

## Commit Boundary

Commit only reflection files and tests after verification passes. Do not change the ProseForge adapter here.
