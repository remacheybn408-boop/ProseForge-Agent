# Task 64: Cross-Platform CI Pipeline

## Goal

Run the test suite automatically on Windows, macOS, and Linux so native-support claims are continuously verified.

## Agent Product Requirement

A product that promises native behavior on three operating systems must prove it on every change, not only by hand.

> Dependency note: execute after the package skeleton (Task 01); strengthen as native cards (49–51, 59) land.

## Architecture Notes

This card adds a GitHub Actions workflow plus a small validator so the matrix is testable without pushing to CI. The validator parses the workflow file and asserts the OS/Python matrix and the pytest step exist; the workflow itself runs `python -m pytest` on each OS. The validator reuses the native QA matrix (Task 59) as the source of truth for which OSes are required, keeping CI and the QA matrix in sync.

Read before starting:

- ../architecture/09-installation-and-native-platforms.md (Acceptance Criteria)
- ../appendices/02-test-matrix.md
- 00-task-index.md

## Files

- Create `.github/workflows/ci.yml`
- Create `src/proseforge_agent/install/ci_matrix.py`
- Create `tests/test_ci_pipeline.py`
- Create `tests/fixtures/cross-platform-ci-pipeline/expected_matrix.json`

## Interfaces / Contracts

- `CIWorkflow.load(path).matrix() -> dict` returns the parsed `os` and `python-version` axes.
- The matrix `os` axis must include a Windows, a macOS, and an Ubuntu runner.
- `CIWorkflow.has_pytest_step() -> bool` confirms a `python -m pytest` step exists.
- `validate_against_qa_matrix(qa_matrix) -> None` raises `ConfigurationError` if a required OS is missing from CI.

## Data Flow

1. Parse `.github/workflows/ci.yml`.
2. Extract the OS and Python matrix axes.
3. Confirm a pytest step is present.
4. Cross-check the OS axis against the native QA matrix.
5. Report any missing OS or step.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_ci_pipeline.py::test_ci_matrix_covers_three_operating_systems`**

```python
def test_ci_matrix_covers_three_operating_systems():
    matrix = CIWorkflow.load(".github/workflows/ci.yml").matrix()
    os_axis = " ".join(matrix["os"]).lower()
    assert "windows" in os_axis
    assert "macos" in os_axis
    assert "ubuntu" in os_axis
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_ci_pipeline.py::test_ci_matrix_covers_three_operating_systems -q
```

Expected: FAIL because `.github/workflows/ci.yml` and `CIWorkflow` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Create the workflow file with the three-OS matrix and a pytest step, and implement `CIWorkflow`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_ci_pipeline.py::test_ci_matrix_covers_three_operating_systems -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_workflow_has_a_pytest_step
test_python_version_axis_includes_minimum_supported
test_validate_against_qa_matrix_flags_missing_os
test_workflow_installs_package_before_tests
test_workflow_file_is_valid_yaml
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_ci_pipeline.py -q
pf-agent qa ci --check
```

Expected: tests pass and `qa ci --check` confirms the CI matrix matches the native QA matrix.

- [ ] **Step 7: Record commit boundary**

```powershell
git add .github/workflows/ci.yml src/proseforge_agent/install/ci_matrix.py tests/test_ci_pipeline.py tests/fixtures/cross-platform-ci-pipeline
git commit -m "feat: add cross-platform ci pipeline"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The workflow runs the suite on Windows, macOS, and Ubuntu runners.
- The validator parses YAML and is platform-agnostic.
- No machine-specific paths appear in the workflow.

## Failure Modes To Prove

- A missing OS in the matrix fails the test.
- A workflow without a pytest step fails the test.
- A CI matrix that drifts from the QA matrix raises `ConfigurationError`.
- The workflow installs the package before running tests.

## Verification

```powershell
python -m pytest tests/test_ci_pipeline.py -q
pf-agent qa ci --check
```

## Acceptance

- CI runs pytest on Windows, macOS, and Linux.
- The CI matrix is validated against the native QA matrix.
- The workflow file is valid YAML with a pytest step.
- Drift between CI and QA matrix is caught.

## Commit Boundary

Commit only the workflow, validator, and tests after verification passes. Do not add deploy or release steps here.
