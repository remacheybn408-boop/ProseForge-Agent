# Task 49: Windows Native Support

## Goal

Make Windows a first-class runtime for install, chat, provider setup, and writing workflows.

## Agent Product Requirement

The user's current environment is Windows, so this cannot be an afterthought.

## Architecture Notes

`windows` contributes the Windows-specific check group used by the doctor (Task 42) and reuses `platform_io` (Task 44), `app_dirs` (Task 43), and `secrets` (Task 45). It detects PowerShell/Windows Terminal UTF-8 capability, Credential Manager availability, long-path support, and paths with spaces. It contains only Windows logic; cross-platform primitives stay in their shared modules so this file is not a second copy of them.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Native Terminal Support, Secret Storage)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/windows.py`
- Create `tests/test_windows_native_support.py`
- Create `tests/fixtures/windows-native-support/env_samples.json`

## Interfaces / Contracts

- `WindowsChecks(env).run() -> list[DoctorCheck]` produces checks named `powershell_utf8`, `credential_manager`, `long_paths`, and `spaces_in_paths`.
- Each check uses the shared `DoctorCheck` type and carries a recovery command when failing.
- When `WT_SESSION` is present, `powershell_utf8` reports `ok`; under bare CMD without UTF-8 it reports `warn` with an ASCII-fallback note.
- Windows logic never duplicates `platform_io`/`app_dirs`; it calls them.

## Data Flow

1. Read the Windows environment (terminal, shell, credential backend).
2. Run each Windows-specific check via shared primitives.
3. Mark ok/warn/fail with details.
4. Attach recovery commands to failures.
5. Return the list of `DoctorCheck` records.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_windows_native_support.py::test_windows_terminal_reports_utf8_capable`**

```python
def test_windows_terminal_reports_utf8_capable():
    checks = {c.name: c for c in WindowsChecks(env={"WT_SESSION": "1"}).run()}
    assert checks["powershell_utf8"].status == "ok"
    assert "credential_manager" in checks
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_windows_native_support.py::test_windows_terminal_reports_utf8_capable -q
```

Expected: FAIL because `WindowsChecks` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `WindowsChecks` reusing `platform_io`, `app_dirs`, and `secrets`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_windows_native_support.py::test_windows_terminal_reports_utf8_capable -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_bare_cmd_without_utf8_warns_with_ascii_fallback
test_credential_manager_unavailable_recommends_env_fallback
test_long_path_check_flags_disabled_long_paths
test_path_with_spaces_is_handled_as_normal
test_chinese_project_path_round_trips
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_windows_native_support.py -q
pf-agent doctor --section windows
```

Expected: tests pass and the `windows` doctor section reports terminal, credential, and path checks.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_windows_native_support.py -q
```

Expected: PASS using simulated Windows environments; no real Windows-only API is required to run the tests.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/windows.py tests/test_windows_native_support.py tests/fixtures/windows-native-support
git commit -m "feat: add windows native support"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Windows checks are driven by a simulated `env` so they test on any host.
- UTF-8 fixtures cover Chinese paths and Windows Terminal.
- Shared primitives are reused, not reimplemented.

## Failure Modes To Prove

- Bare CMD without UTF-8 warns and proposes an ASCII fallback.
- Credential Manager unavailable recommends the env fallback.
- Disabled long-path support is flagged with a recovery command.
- A path with spaces is treated as normal.

## Verification

```powershell
python -m pytest tests/test_windows_native_support.py -q
pf-agent doctor --section windows
```

## Acceptance

- Windows terminal, credential, and path checks work.
- The checks reuse shared cross-platform primitives.
- Recovery commands are Windows-appropriate.
- Tests run on any host via simulated environments.

## Commit Boundary

Commit only Windows-support files and tests after verification passes. Do not duplicate shared path/secret logic here.
