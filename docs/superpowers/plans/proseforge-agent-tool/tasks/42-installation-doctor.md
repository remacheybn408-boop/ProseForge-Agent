# Task 42: Installation Doctor

## Goal

Implement `pf-agent doctor` with actionable platform diagnostics.

## Agent Product Requirement

When setup fails, users need exact recovery commands instead of stack traces.

## Architecture Notes

`InstallationDoctor` runs a fixed set of checks and returns a structured report where every failing check carries a concrete recovery command. It reads config, app dirs (Task 43), platform IO (Task 44), and secret backend status (Task 45), but it is read-only: it never mutates config, secrets, or the workspace. The `--section` flag selects one check group (`paths`, `proseforge`, `providers`, `secrets`, `encoding`, `packaging`). Other install cards reuse this report rather than printing their own diagnostics.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Doctor Checks)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/doctor.py`
- Create `tests/test_installation_doctor.py`
- Create `tests/fixtures/installation-doctor/sample_env.json`

## Interfaces / Contracts

- `InstallationDoctor(env, config=None).run(section: str | None = None) -> DoctorReport`.
- `DoctorReport` holds `checks: list[DoctorCheck]`; each `DoctorCheck` has `name`, `status` (`ok` | `warn` | `fail`), `detail`, `recovery` (command string or `None`).
- Every `fail` check must have a non-empty `recovery` string.
- Checks cover OS, Python, package, config, workspace, ProseForge root, provider keys, secret backend, encoding, and writability.

## Data Flow

1. Gather platform context (OS, Python, encoding) and config.
2. Run the selected section's checks (or all sections).
3. Mark each check ok/warn/fail with a detail.
4. Attach a recovery command to every failing check.
5. Return the `DoctorReport` and render Markdown/JSON.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_installation_doctor.py::test_doctor_reports_missing_proseforge_root_with_recovery`**

```python
def test_doctor_reports_missing_proseforge_root_with_recovery():
    report = InstallationDoctor(env={}).run(section="proseforge")
    check = report.check("proseforge_root")
    assert check.status == "fail"
    assert check.recovery  # a concrete recovery command, not empty
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_installation_doctor.py::test_doctor_reports_missing_proseforge_root_with_recovery -q
```

Expected: FAIL because `InstallationDoctor`, `DoctorReport`, and `DoctorCheck` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `InstallationDoctor`, `DoctorReport`, `DoctorCheck`, section selection, and recovery-command attachment.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_installation_doctor.py::test_doctor_reports_missing_proseforge_root_with_recovery -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_every_failing_check_has_a_recovery_command
test_doctor_section_filter_runs_only_that_group
test_doctor_does_not_mutate_config_or_secrets
test_doctor_report_renders_markdown_and_json
test_doctor_redacts_secret_values_in_output
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_installation_doctor.py -q
pf-agent doctor
pf-agent doctor --section providers
```

Expected: command exits 0, prints a report, and lists a recovery command for each failure.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_installation_doctor.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux environments in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/doctor.py tests/test_installation_doctor.py tests/fixtures/installation-doctor
git commit -m "feat: add installation doctor"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Report paths are relative or env-placeholder based, never absolute machine paths.
- Recovery commands use portable, copy-pasteable forms per platform.
- UTF-8 fixtures cover Chinese config and workspace paths.

## Failure Modes To Prove

- A failing check always carries a recovery command.
- Secret values are redacted in both Markdown and JSON output.
- Doctor never writes to config, secrets, or workspace.
- Unknown `--section` value raises `ConfigurationError`.

## Verification

```powershell
python -m pytest tests/test_installation_doctor.py -q
pf-agent doctor
```

## Acceptance

- `pf-agent doctor` reports platform-specific diagnostics.
- Every failure includes a recovery command.
- Doctor is read-only.
- Report renders as Markdown and JSON.

## Commit Boundary

Commit only doctor files and tests after verification passes. Do not add mutating behavior here.
