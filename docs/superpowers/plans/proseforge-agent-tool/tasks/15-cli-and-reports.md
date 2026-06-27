# Task 15: CLI And Reports

## Goal

Expose stable operator commands and shared report rendering.

## Architecture Notes

CLI and reports are the human operating surface for the agent.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Modify `src/proseforge_agent/cli.py`
- Create `src/proseforge_agent/reports/render.py`
- Create `src/proseforge_agent/reports/registry.py`
- Create `tests/test_cli_commands.py`
- Create `tests/test_reports.py`

## Interfaces / Contracts

Command groups: project, proseforge, provider, memory, retrieve, phase-plan, daily-workbook, chapter, workflow, report, extension. Reports render Markdown, JSON, and terminal summaries with status and next action.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_cli_commands.py::test_cli_lists_required_command_groups`**

```python
def test_cli_lists_required_command_groups(capsys):
    code = main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    for name in ["provider", "memory", "chapter", "workflow", "report"]:
        assert name in out
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_cli_commands.py::test_cli_lists_required_command_groups -q
```

Expected: FAIL because command groups and report renderer are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement argparse command groups, shared output flags, dry-run/write flags, report renderer, report registry, and CLI error formatting.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_cli_commands.py::test_cli_lists_required_command_groups -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_cli_commands.py tests/test_reports.py -q
pf-agent report command-reference --write
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/cli.py tests
git commit -m "feat: add cli commands and reports"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_cli_commands.py tests/test_reports.py -q
pf-agent report command-reference --write
```

## Acceptance

- Help text names required inputs and artifacts.
- Dry-run is available for filesystem-changing commands.
- JSON reports are stable for automation.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
