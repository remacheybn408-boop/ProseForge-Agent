# Task 183: PyPI / TestPyPI Publish

## Goal

Build the distribution artifacts and publish them to TestPyPI first, then PyPI, with a pre-publish readiness gate that blocks broken or duplicate releases.

## Agent Product Requirement

Ordinary users who already have Python should be able to `pipx install proseforge-agent` instead of cloning the repository. That requires a real, repeatable publish path — not just the packaging-readiness checks that Task 47 verifies.

## Architecture Notes

This card supplies the **actual publish** that the 1–60 packaging cards deliberately left out. Task 47 (`package_checks`) proves the install is healthy (console entry point, importability, dependency resolution); this card builds the wheel/sdist and uploads them. It lives in the `release/` subpackage next to the Task 60 gate.

Following the project's testing philosophy, the production code performs the real `build` and `twine upload`, but it accepts an injectable command runner and a `dry_run` mode so tests stay deterministic and offline — no network, no real upload, no real token. Real publishing is performed by a human or CI that supplies credentials at invocation time. This mirrors Task 48, which defines a real build contract without shipping a binary in tests.

The publisher gates on `PackageChecker().verify()` (Task 47) before any upload and selects the target repository (`testpypi` before `pypi`). The release version is read from `pyproject.toml` / `version.py`; publishing a version that already exists on the target index is refused to prevent duplicate releases.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Supported Install Channels)
- 47-pip-pipx-source-installation.md
- 60-complete-agent-release-gate.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/release/publish.py`
- Create `tests/test_pypi_publish.py`
- Create `tests/fixtures/pypi-publish/version_sample.txt`

## Interfaces / Contracts

- `PyPIPublisher(runner, checker)` — `runner` is an injectable command executor; `checker` is a Task 47 `PackageChecker`.
- `PyPIPublisher().plan(repository: str) -> PublishPlan` returns the ordered argv steps: `python -m build` then `twine upload --repository {testpypi|pypi} dist/*`.
- `PublishPlan` exposes `build_command`, `upload_command`, `repository`, and `version`.
- `PyPIPublisher().publish(repository: str, *, dry_run: bool = False) -> PublishReport`.
- `PublishReport` fields: `passed` (bool), `repository`, `version`, `steps`, `skipped`, `summary`.
- `passed` is `True` only when `checker.verify()` passes, the version is not already published, and (when not `dry_run`) build and upload both succeed.
- `repository` must be one of `testpypi` or `pypi`; any other value raises `ConfigurationError`.
- The report and any log line must never contain the API token.

## Data Flow

1. Read the release version from `pyproject.toml` / `version.py`.
2. Run `PackageChecker().verify()` as the pre-publish gate.
3. Refuse if the version already exists on the target repository.
4. Build the wheel/sdist (`python -m build`).
5. Upload via `twine upload --repository {repository}` (skipped under `dry_run`).
6. Return a `PublishReport` with redacted, portable details.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_pypi_publish.py::test_publish_plan_builds_and_uploads_to_selected_repository`**

```python
def test_publish_plan_builds_and_uploads_to_selected_repository():
    publisher = PyPIPublisher(runner=FakeRunner(), checker=PassingChecker())
    plan = publisher.plan(repository="testpypi")
    assert plan.build_command[:3] == ["python", "-m", "build"]
    assert "--repository" in plan.upload_command
    assert "testpypi" in plan.upload_command
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_pypi_publish.py::test_publish_plan_builds_and_uploads_to_selected_repository -q
```

Expected: FAIL because `PyPIPublisher` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `PyPIPublisher`, `PublishPlan`, `PublishReport`, version resolution, the PackageChecker gate, and the injectable runner with `dry_run`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_pypi_publish.py::test_publish_plan_builds_and_uploads_to_selected_repository -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_publish_blocked_when_package_checker_fails
test_publish_refused_when_version_already_exists
test_dry_run_does_not_invoke_real_upload
test_unknown_repository_raises_configuration_error
test_report_and_logs_never_contain_token
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_pypi_publish.py -q
```

Expected: tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/release/publish.py tests/test_pypi_publish.py tests/fixtures/pypi-publish
git commit -m "feat: add real PyPI publish runner"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The `python -m build` / `twine upload` commands are identical across platforms.
- The report contains only logical paths (`dist/*`), never machine-specific absolute paths.
- Credentials are read from the environment / native secret storage at call time, never embedded in the plan.

## Failure Modes To Prove

- A failing `PackageChecker().verify()` blocks publish (`passed=False`, upload skipped).
- A version already present on the target index is refused.
- `dry_run` produces the full plan but performs no real upload.
- An unknown repository raises `ConfigurationError`.
- The token never appears in the report or logs.

## Verification

```powershell
python -m pytest tests/test_pypi_publish.py -q
python -m pytest -q
```

## Acceptance

- The publisher builds artifacts and uploads to TestPyPI/PyPI through an injectable runner.
- The Task 47 readiness gate blocks broken releases; duplicate versions are refused.
- Tests are deterministic and offline; no real network or token is required.
- Existing user data, project artifacts, secrets, and config are preserved.

## Commit Boundary

Commit only the publish runner, its tests, and required fixtures after verification passes. Do not bundle the binary build (Task 184) or installers (Task 185) into this commit.
