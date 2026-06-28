# Task 43: Cross-Platform App Directories

## Goal

Resolve native config, data, cache, log, and portable workspace directories on Windows, macOS, and Linux.

## Agent Product Requirement

Native support starts with putting files where each OS expects them.

## Architecture Notes

`AppDirs` is a pure resolver: given a platform name and an environment mapping, it returns the config, data, cache, and log directories following the matrix in architecture 09, plus a portable `.pf-agent/` mode. It performs no filesystem writes and reads no global state beyond the passed-in environment, so it is fully testable by simulating each OS. First-run (Task 41), doctor (Task 42), and the workspace loader (Task 02) depend on it.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Cross-Platform Directory Rules)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/app_dirs.py`
- Create `tests/test_app_dirs.py`
- Create `tests/fixtures/cross-platform-app-directories/expected_paths.json`

## Interfaces / Contracts

- `AppDirs.for_platform(platform: str, env: dict, portable: bool = False) -> AppDirs`.
- Properties `config_dir`, `data_dir`, `cache_dir`, `log_dir` return `Path` objects following the architecture 09 matrix.
- Linux honours `XDG_*` overrides and falls back to `~/.config`, `~/.local/share`, `~/.cache`, `~/.local/state` when unset.
- `portable=True` roots everything under a single `.pf-agent/` directory regardless of platform.

## Data Flow

1. Receive platform name, environment mapping, and portable flag.
2. Select the per-platform directory rule set.
3. Apply environment overrides (e.g. `XDG_CONFIG_HOME`, `%APPDATA%`).
4. Compute config/data/cache/log paths.
5. Return the resolved `AppDirs` value object.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_app_dirs.py::test_linux_honours_xdg_config_home`**

```python
def test_linux_honours_xdg_config_home():
    dirs = AppDirs.for_platform("linux", env={"XDG_CONFIG_HOME": "/tmp/cfg"})
    assert dirs.config_dir == Path("/tmp/cfg/proseforge-agent")
    fallback = AppDirs.for_platform("linux", env={"HOME": "/home/u"})
    assert fallback.config_dir == Path("/home/u/.config/proseforge-agent")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_app_dirs.py::test_linux_honours_xdg_config_home -q
```

Expected: FAIL because `AppDirs` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `AppDirs`, the per-platform matrix, XDG/`%APPDATA%` overrides, and portable mode.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_app_dirs.py::test_linux_honours_xdg_config_home -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_windows_uses_appdata_for_config_and_localappdata_for_data
test_macos_uses_application_support_and_library_caches
test_portable_mode_roots_everything_under_pf_agent
test_missing_home_raises_configuration_error
test_resolved_paths_preserve_utf8_user_names
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_app_dirs.py -q
pf-agent doctor --section paths
```

Expected: tests pass and the `paths` doctor section prints the resolved directories for the current platform.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_app_dirs.py -q
```

Expected: PASS for the simulated Windows, macOS, and Linux cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/app_dirs.py tests/test_app_dirs.py tests/fixtures/cross-platform-app-directories
git commit -m "feat: add app directories"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Resolver is pure; it simulates each OS through the `platform`/`env` arguments.
- Returned paths preserve UTF-8 user and project names.
- No drive letters or developer paths are hard-coded.

## Failure Modes To Prove

- Missing `HOME`/`%APPDATA%` raises `ConfigurationError` with guidance.
- Unknown platform name raises `ConfigurationError`.
- Portable mode never escapes the `.pf-agent/` root.
- XDG overrides take precedence over defaults.

## Verification

```powershell
python -m pytest tests/test_app_dirs.py -q
pf-agent doctor --section paths
```

## Acceptance

- Config, data, cache, and log dirs match architecture 09 on all three platforms.
- Portable mode is supported.
- Resolver is pure and fully simulated in tests.
- Paths preserve UTF-8 names.

## Commit Boundary

Commit only app-dirs files and tests after verification passes. Do not add filesystem-writing behavior here.
