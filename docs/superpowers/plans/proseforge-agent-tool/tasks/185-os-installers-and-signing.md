# Task 185: OS Installers And Signing

## Goal

Produce and sign native OS installers — Windows `.msi`, macOS `.dmg`, and a Linux `install.sh` — from the standalone binary, with signing that degrades gracefully when credentials are absent.

## Agent Product Requirement

A non-technical user expects a familiar installer for their OS, ideally signed so the OS does not warn about an untrusted publisher. This is the last mile that turns the Task 184 binary into something an ordinary user can double-click.

## Architecture Notes

This card packages the Task 184 binary into per-OS installers and signs them. It reuses `AppDirs` (Task 43, `install/app_dirs.py`) to decide install locations and the Task 184 `BinaryBuilder` output as the payload.

The builder emits the real installer and signing commands (`signtool` on Windows, `codesign`/`productsign` on macOS, `gpg` detached signature for the Linux script) through an injectable command runner with a `dry_run` mode, keeping tests deterministic and offline. Signing is **optional and credential-gated**: when signing credentials are not present, the signing step is warn-skipped rather than failed, so an unsigned-but-valid installer is still produced. Credentials never appear in the recipe, report, or logs.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Supported Install Channels)
- 184-standalone-binary-build.md
- 43-cross-platform-app-directories.md
- 49-windows-native-support.md
- 50-macos-native-support.md
- 51-linux-native-support.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/installers.py`
- Create `tests/test_os_installers.py`
- Create `tests/fixtures/os-installers-and-signing/recipe_sample.json`

## Interfaces / Contracts

- `InstallerBuilder(platform, app_dirs, runner)` — `app_dirs` is a Task 43 `AppDirs`; `runner` is an injectable command executor.
- `InstallerBuilder().recipe() -> InstallerRecipe` returns the per-platform package command and the signing command.
- `InstallerRecipe` exposes `artifact_name` (`.msi` / `.dmg` / `install.sh`), `package_command`, `sign_command`, and `install_dir` (from `AppDirs`).
- `InstallerBuilder().build(*, sign: bool = True, dry_run: bool = False) -> InstallerReport`.
- `InstallerReport` fields: `passed` (bool), `artifact_name`, `signed` (bool), `steps`, `skipped`, `summary`.
- When `sign=True` but no signing credential is available, `signed=False`, the step is recorded in `skipped` with a warning, and `passed` stays `True`.
- An unknown platform raises `ConfigurationError`.
- Signing credentials never appear in the recipe, report, or logs.

## Data Flow

1. Select the per-platform installer recipe and `install_dir` from `AppDirs`.
2. Build the installer package from the Task 184 binary payload (skipped under `dry_run`).
3. Detect signing credentials; sign if present, otherwise warn-skip.
4. Return an `InstallerReport` with redacted, portable details.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_os_installers.py::test_windows_recipe_produces_msi_and_uses_app_dirs_install_path`**

```python
def test_windows_recipe_produces_msi_and_uses_app_dirs_install_path():
    builder = InstallerBuilder(platform="windows", app_dirs=FakeAppDirs(), runner=FakeRunner())
    recipe = builder.recipe()
    assert recipe.artifact_name.endswith(".msi")
    assert recipe.install_dir  # resolved from AppDirs
    assert recipe.sign_command  # signtool invocation defined
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_os_installers.py::test_windows_recipe_produces_msi_and_uses_app_dirs_install_path -q
```

Expected: FAIL because `InstallerBuilder` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `InstallerBuilder`, `InstallerRecipe`, `InstallerReport`, per-platform packaging/signing commands, AppDirs-derived install paths, the injectable runner with `dry_run`, and credential-gated signing.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_os_installers.py::test_windows_recipe_produces_msi_and_uses_app_dirs_install_path -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_macos_recipe_produces_dmg
test_linux_recipe_produces_install_script
test_signing_skipped_with_warning_when_no_credentials
test_dry_run_does_not_invoke_real_packager
test_unknown_platform_raises_configuration_error
test_recipe_and_report_never_contain_signing_secret
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_os_installers.py -q
pf-agent doctor --section packaging
```

Expected: tests pass and the packaging section reports installer readiness for the current platform.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/installers.py tests/test_os_installers.py tests/fixtures/os-installers-and-signing
git commit -m "feat: add OS installers and signing"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Installer artifact and signing tool follow each platform's convention (`.msi`/signtool, `.dmg`/codesign, `install.sh`/gpg).
- Install paths come from `AppDirs`, never hard-coded absolute machine paths.
- The same `InstallerReport` shape is returned on every platform.

## Failure Modes To Prove

- Missing signing credentials warn-skip rather than fail; the installer is still produced unsigned.
- Signing secrets never appear in the recipe, report, or logs.
- `dry_run` produces the recipe without invoking the real packager.
- An unknown platform raises `ConfigurationError`.
- Install paths resolve through `AppDirs`.

## Verification

```powershell
python -m pytest tests/test_os_installers.py -q
python -m pytest -q
```

## Acceptance

- Per-OS installers (`.msi` / `.dmg` / `install.sh`) are produced from the Task 184 binary.
- Signing runs when credentials exist and degrades gracefully when they do not.
- Install locations come from `AppDirs`; secrets are never leaked.
- Tests are deterministic and offline via the injectable runner.
- Existing user data, project artifacts, secrets, and config are preserved.

## Commit Boundary

Commit only the installer builder, its tests, and required fixtures after verification passes. Do not bundle the publish runner (Task 183) or binary build (Task 184) into this commit.
