# Task 47: pip, pipx, And Source Installation

## Goal

Document and verify source, pip, and pipx install flows.

## Agent Product Requirement

Engineers and non-engineers need reliable install commands before trying chat or writing workflows.

## Architecture Notes

`package_checks` inspects the installed package metadata to prove the install is healthy: the console entry point exists, dependency groups resolve, and the editable/source layout is importable. The checks read distribution metadata (via `importlib.metadata`) rather than shelling out to pip, so they run fast and offline. The installation doctor (Task 42) `packaging` section reuses these checks.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Supported Install Channels)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/package_checks.py`
- Create `tests/test_python_install_flows.py`
- Create `tests/fixtures/pip-pipx-source-installation/metadata_sample.json`

## Interfaces / Contracts

- `PackageChecker().console_scripts() -> dict[str, str]` returns entry-point name to target.
- `PackageChecker().verify() -> PackageReport` with `checks` for `console_script`, `import`, `dependencies`, and `python_version`.
- `console_scripts()` must include `pf-agent` mapped to `proseforge_agent.cli:main`.
- Checks read metadata only; they do not invoke pip or the network.

## Data Flow

1. Read distribution metadata for `proseforge-agent`.
2. Confirm the `pf-agent` console entry point and its target.
3. Confirm the package imports under the src-layout.
4. Confirm declared dependency groups resolve.
5. Return a `PackageReport`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_python_install_flows.py::test_console_entrypoint_maps_pf_agent_to_cli_main`**

```python
def test_console_entrypoint_maps_pf_agent_to_cli_main():
    scripts = PackageChecker().console_scripts()
    assert scripts["pf-agent"] == "proseforge_agent.cli:main"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_python_install_flows.py::test_console_entrypoint_maps_pf_agent_to_cli_main -q
```

Expected: FAIL because `PackageChecker` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `PackageChecker`, `PackageReport`, and metadata-based checks.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_python_install_flows.py::test_console_entrypoint_maps_pf_agent_to_cli_main -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_package_imports_under_src_layout
test_declared_dependencies_resolve
test_python_version_meets_minimum
test_packaging_report_lists_failed_checks_with_recovery
test_report_paths_are_portable
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_python_install_flows.py -q
pf-agent doctor --section packaging
```

Expected: tests pass and the `packaging` doctor section confirms the console script and imports.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_python_install_flows.py -q
```

Expected: PASS regardless of platform (metadata-only checks).

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/package_checks.py tests/test_python_install_flows.py tests/fixtures/pip-pipx-source-installation
git commit -m "feat: add python install flows"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Checks use `importlib.metadata`, not pip subprocess calls.
- Report paths are relative, never absolute machine paths.
- Works identically on Windows, macOS, and Linux.

## Failure Modes To Prove

- Missing console entry point is reported as a failed check with a recovery command.
- Unresolved dependency group is reported, not raised as a bare traceback.
- Python below the minimum is reported with the required version.
- Report contains no machine-specific absolute paths.

## Verification

```powershell
python -m pytest tests/test_python_install_flows.py -q
pf-agent doctor --section packaging
```

## Acceptance

- The `pf-agent` console entry point is verified.
- Import, dependencies, and Python version are checked.
- Checks run offline.
- The doctor reuses these checks.

## Commit Boundary

Commit only package-check files and tests after verification passes. Do not change build configuration here.
