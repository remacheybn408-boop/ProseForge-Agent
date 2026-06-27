# Task 41: First-Run Onboarding Wizard

## Goal

Implement `pf-agent init` for portable first-run setup.

## Agent Product Requirement

Users on every OS need a guided path from install to usable chat and writing workflows.

## Architecture Notes

`FirstRunWizard` implements `pf-agent init`. It detects OS, terminal encoding, and Python, chooses the app data directory (native or portable `.pf-agent/`), detects or prompts for `PROSEFORGE_ROOT`, writes config and workspace, stubs a provider profile, and runs the doctor (Task 42) to produce a first-run report. Config must store `PROSEFORGE_ROOT` as an environment placeholder, never the developer's absolute path. It depends on `AppDirs` (Task 43), config (Task 02), and the doctor (Task 42); it does not call providers or the network.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (First Run Flow)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/first_run.py`
- Create `tests/test_first_run_onboarding.py`
- Create `tests/fixtures/first-run-onboarding-wizard/expected_config.yaml`

## Interfaces / Contracts

- `FirstRunWizard(root, app_dirs, doctor).run(inputs: dict) -> FirstRunResult`.
- `FirstRunResult` fields: `config_path`, `workspace_path`, `provider_stub_path`, `doctor_report_path`, `mode` (`portable` | `native`).
- The written config references `${PROSEFORGE_ROOT}` (or `${PROSEFORGE_AGENT_WORKSPACE:-.pf-agent}`), never an absolute machine path.
- Re-running on an existing install is non-destructive: it reports "already initialized" and does not overwrite config or workspace.

## Data Flow

1. Detect OS, Python, and terminal encoding.
2. Resolve app data directory (native or portable) via `AppDirs`.
3. Detect or accept `PROSEFORGE_ROOT` as an environment placeholder.
4. Write config and create the workspace tree.
5. Write a provider stub and run the doctor.
6. Return `FirstRunResult` with all artifact paths.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_first_run_onboarding.py::test_first_run_writes_portable_config_with_env_root`**

```python
def test_first_run_writes_portable_config_with_env_root(tmp_path):
    result = FirstRunWizard.portable(tmp_path).run(inputs={"proseforge_root": "${PROSEFORGE_ROOT}"})
    config_text = result.config_path.read_text(encoding="utf-8")
    assert "${PROSEFORGE_ROOT}" in config_text
    assert str(tmp_path.drive) not in config_text  # no hard-coded drive/absolute path
    assert result.mode == "portable"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_first_run_onboarding.py::test_first_run_writes_portable_config_with_env_root -q
```

Expected: FAIL because `FirstRunWizard` and `FirstRunResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `FirstRunWizard`, `FirstRunResult`, env-placeholder config writing, workspace creation, provider stub, and doctor invocation.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_first_run_onboarding.py::test_first_run_writes_portable_config_with_env_root -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_rerun_on_existing_install_is_non_destructive
test_native_mode_uses_app_dirs_config_path
test_first_run_creates_full_workspace_tree
test_first_run_report_lists_every_written_artifact
test_first_run_supports_utf8_project_root_paths
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_first_run_onboarding.py -q
pf-agent init --portable --proseforge-root "${PROSEFORGE_ROOT}" --non-interactive
```

Expected: command exits 0, writes a portable config and workspace, and prints the artifacts it created.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_first_run_onboarding.py -q
```

Expected: PASS for the simulated Windows, macOS, and Linux app-dir cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/first_run.py tests/test_first_run_onboarding.py tests/fixtures/first-run-onboarding-wizard
git commit -m "feat: add first run onboarding"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Config uses environment placeholders, never absolute machine paths.
- Workspace tree creation works on Windows, macOS, and Linux.
- UTF-8 fixtures cover Chinese project-root paths.

## Failure Modes To Prove

- Re-running on an existing install does not overwrite config or workspace.
- Unwritable target directory yields a recovery command, not a stack trace.
- Missing `PROSEFORGE_ROOT` prompts for it (interactive) or fails clearly (non-interactive).
- Config never contains a hard-coded drive letter or developer path.

## Verification

```powershell
python -m pytest tests/test_first_run_onboarding.py -q
pf-agent init --portable --proseforge-root "${PROSEFORGE_ROOT}" --non-interactive
```

## Acceptance

- `pf-agent init` creates a working portable config and workspace.
- Config stores `PROSEFORGE_ROOT` as an environment placeholder.
- Re-run is non-destructive.
- First-run report lists all created artifacts.

## Commit Boundary

Commit only first-run files and tests after verification passes. Do not add provider or workflow behavior here.
