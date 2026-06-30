# Task 184: Standalone Binary Build

## Goal

Run a real PyInstaller build that produces the standalone binary described by the Task 48 manifest, then prove it with the post-build smoke command.

## Agent Product Requirement

Users without any Python workflow knowledge need a single-file binary they can download and run. Task 48 defines and validates the binary manifest contract; this card turns that contract into an actual artifact.

## Architecture Notes

This card supplies the **actual build** that Task 48 explicitly defers ("this card does not run a real build in tests"). It consumes the Task 48 `BinaryManifest` (`install/binary_packaging.py`) for the entry point, artifact name, and bundled files, and reuses `AppDirs` (Task 43, `install/app_dirs.py`) so the produced binary resolves native paths at runtime.

The builder performs the real PyInstaller invocation but accepts an injectable command runner and a `dry_run` mode, keeping tests deterministic and offline. The build is followed by the manifest's smoke command (`pf-agent --version`); a failed smoke marks the build as not passing. Real builds run per platform on CI (Task 64) or by a maintainer.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Supported Install Channels)
- 48-standalone-binary-packaging.md
- 43-cross-platform-app-directories.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/binary_build.py`
- Create `tests/test_binary_build.py`
- Create `tests/fixtures/standalone-binary-build/manifest_sample.json`

## Interfaces / Contracts

- `BinaryBuilder(manifest, runner)` — `manifest` is a Task 48 `BinaryManifest`; `runner` is an injectable command executor.
- `BinaryBuilder().build_command() -> list[str]` returns the PyInstaller argv derived from the manifest: `--name {artifact stem}`, `--onefile`, the `entry_point` target, and `--add-data` entries for each bundled file.
- `BinaryBuilder().build(*, dry_run: bool = False) -> BuildReport` runs the build and then the manifest `smoke_command`.
- `BuildReport` fields: `passed` (bool), `artifact_name`, `steps`, `smoke_ok`, `summary`.
- `passed` is `True` only when the manifest validates, the build step succeeds (or `dry_run`), and the smoke command succeeds.
- An unknown platform/arch (from the manifest) raises `ConfigurationError`.
- The report contains no machine-specific absolute paths.

## Data Flow

1. Validate the `BinaryManifest` (reusing Task 48 `validate()`).
2. Compute the PyInstaller `build_command()` from the manifest.
3. Run the build via the injectable runner (skipped under `dry_run`).
4. Run the post-build smoke command (`pf-agent --version`).
5. Return a `BuildReport` with portable details.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_binary_build.py::test_build_command_matches_manifest_entry_point_and_name`**

```python
def test_build_command_matches_manifest_entry_point_and_name():
    manifest = BinaryManifest(platform="windows", arch="x64")
    builder = BinaryBuilder(manifest=manifest, runner=FakeRunner())
    argv = builder.build_command()
    assert "proseforge_agent.cli:main" in " ".join(argv) or "proseforge_agent" in " ".join(argv)
    assert any(part.endswith(".exe") or "pf-agent" in part for part in argv)
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_binary_build.py::test_build_command_matches_manifest_entry_point_and_name -q
```

Expected: FAIL because `BinaryBuilder` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `BinaryBuilder`, `BuildReport`, the PyInstaller command derivation, the injectable runner with `dry_run`, and the post-build smoke step.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_binary_build.py::test_build_command_matches_manifest_entry_point_and_name -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_build_blocked_when_manifest_invalid
test_smoke_failure_marks_build_not_passed
test_dry_run_does_not_invoke_real_pyinstaller
test_unknown_platform_or_arch_raises_configuration_error
test_report_paths_are_portable
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_binary_build.py -q
pf-agent doctor --section packaging
```

Expected: tests pass and the packaging section reports binary build readiness for the current platform.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/binary_build.py tests/test_binary_build.py tests/fixtures/standalone-binary-build
git commit -m "feat: add real standalone binary build"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- The build command derives the artifact name from the per-platform manifest (`.exe` on Windows; no extension on macOS/Linux).
- The smoke command is the same shape (`pf-agent --version`) on all platforms.
- Report paths are relative or logical, never absolute machine paths.

## Failure Modes To Prove

- An invalid manifest blocks the build (`passed=False`).
- A failed smoke command marks the build not passed.
- `dry_run` produces the command without invoking PyInstaller.
- Unknown platform/arch raises `ConfigurationError`.
- The report contains no machine-specific absolute paths.

## Verification

```powershell
python -m pytest tests/test_binary_build.py -q
python -m pytest -q
```

## Acceptance

- A real PyInstaller command is derived from and consistent with the Task 48 manifest.
- The post-build smoke command gates success.
- Tests are deterministic and offline via the injectable runner.
- Existing user data, project artifacts, secrets, and config are preserved.

## Commit Boundary

Commit only the binary-build runner, its tests, and required fixtures after verification passes. Do not bundle the publish runner (Task 183) or installers (Task 185) into this commit.
