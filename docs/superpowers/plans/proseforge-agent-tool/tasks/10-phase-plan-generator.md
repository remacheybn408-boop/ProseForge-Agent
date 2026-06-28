# Task 10: Phase Plan Generator

## Goal

Generate structured professional novel phase plans from intake, memory, and market constraints.

## Architecture Notes

Planning artifacts are machine-checkable project state and feed daily workbooks.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/planning/intake.py`
- Create `src/proseforge_agent/planning/phase_plan.py`
- Create `tests/test_phase_plan_generator.py`
- Create `tests/fixtures/planning/intake.yaml`

## Interfaces / Contracts

`ProjectIntake` captures genre, market, length, cadence, tone, audience, constraints. `PhasePlan` contains volume arcs, chapter ranges, gates, deliverables, and source references.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_phase_plan_generator.py::test_phase_plan_contains_gates_and_chapter_ranges`**

```python
def test_phase_plan_contains_gates_and_chapter_ranges(fake_provider, memory_store):
    plan = PhasePlanGenerator(fake_provider, memory_store).generate(ProjectIntake(slug="demo", title="Demo", genre="fantasy", target_chapters=12))
    assert plan.volumes[0].chapter_start == 1
    assert plan.acceptance_gates
    assert plan.source_references is not None
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_phase_plan_generator.py::test_phase_plan_contains_gates_and_chapter_ranges -q
```

Expected: FAIL because planning module is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement intake validation, planner prompt contract, fake-provider parser, structured phase plan model, repair-on-invalid-output, and report rendering.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_phase_plan_generator.py::test_phase_plan_contains_gates_and_chapter_ranges -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_phase_plan_generator.py -q
pf-agent phase-plan --project demo --level volume --write --provider fake
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/planning/intake.py tests
git commit -m "feat: add phase plan generator"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_phase_plan_generator.py -q
pf-agent phase-plan --project demo --level volume --write --provider fake
```

## Acceptance

- Plans include stage deliverables and acceptance gates.
- Invalid model output is rejected with a parse report.
- Generated plans cite memory or intake sources.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
