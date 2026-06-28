# Task 67: Cross-Module Contract And Golden Regression Tests

## Goal

Pin the interfaces between subsystems with contract tests, and pin deterministic outputs with golden snapshots, so a change in one module breaks loudly and locally instead of surfacing as a late integration bug.

## Agent Product Requirement

A 65-module agent must catch cross-module regressions early and point at the exact broken boundary, or maintenance cost compounds as the product grows.

> Dependency note: establish the canonical fakes early (after Task 04), then add contract/golden cases as each subsystem lands. CI (Task 64) and the release gate (Task 60) consume this tier.

## Architecture Notes

This card creates two things. First, `src/proseforge_agent/testing/fakes.py`: the single authoritative set of fakes (`FakeProvider` reusing `llm/fake.py`, plus `FakeTools`, `FakeSessionStore`, `FakeKernel`, `FakeHTTP`, `FakeRetrieval`) so cards stop defining drifting local fakes (it supplies the `fake_session_store`/`fake_tools` that Task 31 references). Second, two test tiers: `tests/contracts/` asserts each cross-subsystem interface holds, and `tests/golden/` asserts deterministic outputs match stored snapshots. These tiers implement the Internal Interface Compatibility Policy in `architecture/10-modularity-and-recovery.md`.

Read before starting:

- ../architecture/02-system-architecture.md (First Release Interfaces, Hardening Interfaces)
- ../architecture/10-modularity-and-recovery.md (Interface Compatibility Policy)
- ../appendices/02-test-matrix.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/testing/__init__.py`
- Create `src/proseforge_agent/testing/fakes.py`
- Create `tests/contracts/test_boundary_contracts.py`
- Create `tests/golden/test_golden_outputs.py`
- Create `tests/golden/snapshots/` (stored golden artifacts)

## Interfaces / Contracts

- `testing.fakes` exposes the canonical fakes; they satisfy the same `Protocol`s as the real subsystems (`LLMProvider`, tool registry, session store, retrieval).
- Each boundary contract test asserts the *shape* of the data crossing it (required fields/types of `AgentTurnResult`, `GenerationResult`, evidence pack, workflow step result), using only the canonical fakes.
- Golden tests compare deterministic outputs (fake-provider chapter run, evidence pack, daily workbook) to stored snapshots; a mismatch fails with a readable diff.
- A contract failure message names the broken boundary (e.g. `kernel<->provider`).

## Data Flow

1. Build the subsystem under test with canonical fakes for its dependencies.
2. Exercise the boundary (one call across the interface).
3. Assert the crossing data satisfies the interface contract.
4. For golden tests, render the deterministic output and diff against the snapshot.
5. Report the specific boundary or snapshot that failed.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/contracts/test_boundary_contracts.py::test_kernel_provider_contract_holds_with_canonical_fakes`**

```python
from proseforge_agent.testing.fakes import FakeProvider, FakeTools, FakeSessionStore

def test_kernel_provider_contract_holds_with_canonical_fakes():
    kernel = AgentKernel(provider=FakeProvider(), tools=FakeTools(), session_store=FakeSessionStore())
    result = kernel.run_turn(AgentTurnRequest(session_id="new", text="hi",
                                              mode="general_chat", project_slug=None,
                                              permission_level="read_only"))
    # AgentTurnResult contract fields must all be present
    for field in ("text", "intent", "tool_calls", "evidence_refs", "events"):
        assert hasattr(result, field)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/contracts/test_boundary_contracts.py::test_kernel_provider_contract_holds_with_canonical_fakes -q
```

Expected: FAIL because `proseforge_agent.testing.fakes` does not exist yet.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `testing/fakes.py` canonical fakes and the first boundary contract test.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/contracts/test_boundary_contracts.py::test_kernel_provider_contract_holds_with_canonical_fakes -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_kernel_tools_boundary_contract
test_retrieval_memory_boundary_contract
test_workflow_engine_adapter_boundary_contract
test_chat_kernel_boundary_contract
test_golden_fake_provider_chapter_run_matches_snapshot
test_golden_evidence_pack_matches_snapshot
test_contract_failure_message_names_the_broken_boundary
test_canonical_fakes_are_reused_not_redefined_per_card
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/contracts tests/golden -q
pf-agent release check --complete-agent --write-report
```

Expected: contract and golden tiers pass and are included in the release gate's required gates.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/contracts tests/golden -q
```

Expected: PASS on Windows, macOS, and Linux; snapshots are UTF-8 and path-agnostic.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/testing tests/contracts tests/golden
git commit -m "feat: add cross-module contract and golden regression tests"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Golden snapshots are UTF-8 and contain no absolute machine paths.
- Canonical fakes are deterministic and network-free.
- Contract tests run identically on all three platforms.

## Failure Modes To Prove

- Changing one side of a boundary fails its contract test, not a distant integration test.
- A drifted deterministic output fails the golden test with a readable diff.
- The failure message identifies the specific broken boundary.
- Cards reuse the canonical fakes instead of redefining their own.

## Verification

```powershell
python -m pytest tests/contracts tests/golden -q
pf-agent release check --complete-agent --write-report
```

## Acceptance

- Each cross-subsystem boundary has a contract test.
- Deterministic outputs have golden snapshots.
- The contract and golden tiers are required gates in CI and release.
- One authoritative set of fakes is shared across cards.

## Commit Boundary

Commit only the testing helpers and the contract/golden tiers after verification passes. Migrate existing cards to the canonical fakes incrementally, not in this card.
