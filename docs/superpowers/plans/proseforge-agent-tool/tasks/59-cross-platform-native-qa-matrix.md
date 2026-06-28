# Task 59: Cross-Platform Native QA Matrix

## Goal

Define the automated and manual QA matrix for Windows, macOS, and Linux native support.

## Agent Product Requirement

Native support is not real until install, chat, provider setup, paths, secrets, and uninstall are tested on each OS.

## Architecture Notes

`qa_matrix` is the machine-readable definition of what "native support verified" means: for each OS, the required checks, the command to run, and the expected artifact. It is the data the CI pipeline (Task 64) executes and the release gate (Task 60) asserts against. It defines the matrix and validates coverage; it does not itself run platform commands. Each matrix entry maps to an existing card's verification.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Acceptance Criteria)
- ../appendices/02-test-matrix.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/qa_matrix.py`
- Create `tests/test_native_qa_matrix.py`
- Create `tests/fixtures/cross-platform-native-qa-matrix/expected_matrix.json`

## Interfaces / Contracts

- `NativeQAMatrix.required_checks() -> dict[str, list[QACheck]]` keyed by `windows`, `macos`, `linux`.
- `QACheck` fields: `name`, `command`, `expected_artifact`, `automated` (bool).
- Each OS must include at least `install`, `chat`, `doctor`, and `uninstall` checks.
- `validate_coverage(cards) -> CoverageReport` fails if any required check has no backing card verification.

## Data Flow

1. Define the per-OS required check list.
2. Map each check to a command and expected artifact.
3. Mark whether each check is automated or manual.
4. Validate that every check is backed by a card.
5. Return the matrix and a coverage report.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_native_qa_matrix.py::test_each_os_requires_install_chat_doctor_uninstall`**

```python
def test_each_os_requires_install_chat_doctor_uninstall():
    matrix = NativeQAMatrix.required_checks()
    for os_name in ("windows", "macos", "linux"):
        names = {c.name for c in matrix[os_name]}
        assert {"install", "chat", "doctor", "uninstall"}.issubset(names)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_native_qa_matrix.py::test_each_os_requires_install_chat_doctor_uninstall -q
```

Expected: FAIL because `NativeQAMatrix` and `QACheck` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `NativeQAMatrix`, `QACheck`, `CoverageReport`, and the per-OS matrix.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_native_qa_matrix.py::test_each_os_requires_install_chat_doctor_uninstall -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_every_check_maps_to_a_command_and_expected_artifact
test_validate_coverage_fails_when_a_check_has_no_backing_card
test_automated_and_manual_checks_are_distinguished
test_matrix_includes_paths_and_secrets_checks_per_os
test_matrix_report_uses_portable_paths
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_native_qa_matrix.py -q
pf-agent qa matrix --show
```

Expected: tests pass and the command prints the per-OS QA matrix with commands and expected artifacts.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_native_qa_matrix.py -q
```

Expected: PASS; the matrix definition is platform-agnostic data.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/qa_matrix.py tests/test_native_qa_matrix.py tests/fixtures/cross-platform-native-qa-matrix
git commit -m "feat: add native qa matrix"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The matrix is data; it runs on any host.
- Commands and artifacts use portable forms, no absolute paths.
- UTF-8 fixtures cover Chinese expected-artifact names.

## Failure Modes To Prove

- Missing `install`/`chat`/`doctor`/`uninstall` for any OS fails the test.
- A check with no backing card fails `validate_coverage`.
- Automated vs manual checks are clearly distinguished.
- Report contains no machine-specific absolute paths.

## Verification

```powershell
python -m pytest tests/test_native_qa_matrix.py -q
pf-agent qa matrix --show
```

## Acceptance

- Each OS has install/chat/doctor/uninstall checks plus paths/secrets.
- Every check maps to a command and expected artifact.
- Coverage validation catches unbacked checks.
- CI and the release gate consume this matrix.

## Commit Boundary

Commit only QA-matrix files and tests after verification passes. Do not run real platform commands here.
