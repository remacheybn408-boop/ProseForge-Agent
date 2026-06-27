# Task 29: Provider Fallback Router

## Goal

Route roles across providers by capability, privacy, cost, locality, and reliability.

## Architecture Notes

Fallback must explain why each provider was selected or skipped.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/router.py`
- Create `src/proseforge_agent/llm/policies.py`
- Create `tests/test_provider_router.py`
- Create `tests/fixtures/providers/route_matrix.yaml`

## Interfaces / Contracts

Policy modes: default, domestic_only, foreign_only, local_only, privacy_strict, low_cost, high_quality, manual_override. Roles: planner, drafter, critic, reviser, memory, embedding, market_analyst, researcher, code_assistant.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_router.py::test_privacy_strict_policy_blocks_remote_provider_for_sensitive_memory`**

```python
def test_privacy_strict_policy_blocks_remote_provider_for_sensitive_memory(route_matrix):
    decision = ProviderRouter(route_matrix).select(role="memory", policy="privacy_strict", privacy_class="local_only")
    assert decision.selected.family == "fake"
    assert any(skip.reason == "privacy_policy" for skip in decision.skipped)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_router.py::test_privacy_strict_policy_blocks_remote_provider_for_sensitive_memory -q
```

Expected: FAIL because provider router is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement route policies, capability checks, certification checks, missing-key skips, retryable fallback, non-retryable stop, manual override audit, and route reports.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_provider_router.py::test_privacy_strict_policy_blocks_remote_provider_for_sensitive_memory -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_provider_router.py -q
pf-agent provider routes --all-policies --write-report
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/router.py tests
git commit -m "feat: add provider fallback router"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_router.py -q
pf-agent provider routes --all-policies --write-report
```

## Acceptance

- Every role has a selected provider or blocked reason.
- Domestic-only and foreign-only modes are enforced.
- Provider attempts are recorded in workflow state.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
