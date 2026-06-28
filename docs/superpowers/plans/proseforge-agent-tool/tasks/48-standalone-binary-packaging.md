# Task 48: Standalone Binary Packaging

## Goal

Define and verify standalone binary packaging for users without Python workflow knowledge.

## Agent Product Requirement

A native-feeling agent should eventually run as a single command binary on all supported operating systems.

## Architecture Notes

`binary_packaging` describes, and verifies the manifest for, a standalone binary build (PyInstaller-style) per platform/arch. This card does not run a real build in tests; it validates the manifest contract — artifact name, entry point, bundled license/metadata files, and the post-build smoke command — so CI (Task 64) and the release gate (Task 60) can assert packaging readiness without shipping a binary. It reuses `AppDirs` (Task 43) so the bundled binary resolves native paths at runtime.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Supported Install Channels)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/binary_packaging.py`
- Create `tests/test_binary_packaging.py`
- Create `tests/fixtures/standalone-binary-packaging/manifest_sample.json`

## Interfaces / Contracts

- `BinaryManifest(platform, arch)` exposes `artifact_name`, `entry_point`, `bundled_files`, and `smoke_command`.
- Windows artifact name ends with `.exe`; macOS/Linux artifact names have no extension.
- `entry_point` is `proseforge_agent.cli:main`; `bundled_files` includes the license and package metadata.
- `validate() -> ManifestReport` fails if any required asset or the smoke command is missing.

## Data Flow

1. Select the platform/arch manifest rules.
2. Compute the artifact name and entry point.
3. List required bundled files (license, metadata).
4. Define the post-build smoke command (`pf-agent --version`).
5. Validate completeness and return a `ManifestReport`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_binary_packaging.py::test_windows_artifact_name_has_exe_and_entry_point`**

```python
def test_windows_artifact_name_has_exe_and_entry_point():
    manifest = BinaryManifest(platform="windows", arch="x64")
    assert manifest.artifact_name.endswith(".exe")
    assert manifest.entry_point == "proseforge_agent.cli:main"
    assert manifest.smoke_command  # non-empty post-build check
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_binary_packaging.py::test_windows_artifact_name_has_exe_and_entry_point -q
```

Expected: FAIL because `BinaryManifest` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `BinaryManifest`, `ManifestReport`, per-platform naming, and manifest validation.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_binary_packaging.py::test_windows_artifact_name_has_exe_and_entry_point -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_macos_and_linux_artifact_names_have_no_extension
test_manifest_includes_license_and_metadata_files
test_validate_fails_when_smoke_command_missing
test_unknown_platform_or_arch_raises_configuration_error
test_manifest_report_paths_are_portable
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_binary_packaging.py -q
pf-agent doctor --section packaging
```

Expected: tests pass and the packaging section reports binary manifest readiness for the current platform.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_binary_packaging.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux manifests in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/binary_packaging.py tests/test_binary_packaging.py tests/fixtures/standalone-binary-packaging
git commit -m "feat: add binary packaging"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Artifact naming follows each platform's convention.
- Manifest paths are relative or logical, never absolute machine paths.
- Smoke command is the same shape (`pf-agent --version`) on all platforms.

## Failure Modes To Prove

- A manifest missing the smoke command fails validation.
- Unknown platform/arch raises `ConfigurationError`.
- Missing license/metadata files fail validation.
- Report contains no machine-specific absolute paths.

## Verification

```powershell
python -m pytest tests/test_binary_packaging.py -q
pf-agent doctor --section packaging
```

## Acceptance

- Per-platform artifact naming is correct.
- Manifest lists entry point, license, metadata, and smoke command.
- Validation fails on missing assets.
- CI and release gate can assert packaging readiness.

## Commit Boundary

Commit only binary-packaging files and tests after verification passes. Do not add a real build pipeline here.
