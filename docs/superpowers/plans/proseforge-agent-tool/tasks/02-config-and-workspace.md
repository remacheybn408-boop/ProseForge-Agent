# Task 02: Config And Workspace

## Goal

Load environment-variable based config and resolve workspace paths without hard-coded machine folders.

## Architecture Notes

Configuration is the portability boundary. ProseForge root is supplied by config or environment, never by a baked-in local path.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `configs/agent.example.yaml`
- Create `src/proseforge_agent/config.py`
- Create `src/proseforge_agent/workspace.py`
- Create `tests/test_config.py`
- Create `tests/test_workspace.py`

## Interfaces / Contracts

Example config uses `paths.proseforge_root: "${PROSEFORGE_ROOT}"` and `paths.workspace_root: "${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}"`; relative paths resolve from the config file directory.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_config.py::test_load_agent_config_expands_environment_paths`**

```python
def test_load_agent_config_expands_environment_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("PROSEFORGE_ROOT", str(tmp_path / "engine"))
    cfg_file = tmp_path / "agent.yaml"
    cfg_file.write_text(
        """paths:
  proseforge_root: ${PROSEFORGE_ROOT}
  workspace_root: ${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}
project:
  slug: demo
  title: Demo
""",
        encoding="utf-8",
    )
    cfg = load_agent_config(cfg_file)
    assert cfg.proseforge_root == tmp_path / "engine"
    assert cfg.workspace_root == tmp_path / ".pf-agent"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_config.py::test_load_agent_config_expands_environment_paths -q
```

Expected: FAIL with `NameError` or missing `load_agent_config`.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `AgentConfig`, `${VAR}` and `${VAR:-default}` expansion, required-field errors, `WorkspaceLayout.ensure()`, and the portable example config.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_config.py::test_load_agent_config_expands_environment_paths -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_config.py tests/test_workspace.py -q
pf-agent doctor --config configs/agent.example.yaml --dry-run
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add configs/agent.example.yaml tests
git commit -m "feat: add portable config and workspace layout"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_config.py tests/test_workspace.py -q
pf-agent doctor --config configs/agent.example.yaml --dry-run
```

## Acceptance

- No config sample contains an author machine path.
- Missing `project.slug` reports `project.slug` in the error.
- Workspace directories are explicit: projects, phase_plans, daily_workbooks, evidence_packs, workflow_runs, reports, logs.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
