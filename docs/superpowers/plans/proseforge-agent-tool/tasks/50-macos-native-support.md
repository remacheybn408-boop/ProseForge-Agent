# Task 50: macOS Native Support

## Goal

Make macOS a first-class runtime for install, chat, provider setup, and writing workflows.

## Agent Product Requirement

macOS users expect Keychain, Application Support paths, zsh completions, and universal binary awareness.

## Architecture Notes

`macos` contributes the macOS-specific check group used by the doctor (Task 42) and reuses `platform_io` (Task 44), `app_dirs` (Task 43), and `secrets` (Task 45). It detects Keychain availability, Application Support / Caches / Logs locations, the active zsh shell, and Gatekeeper/universal-binary notes for the standalone binary. macOS-only logic lives here; shared primitives are called, not copied.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Cross-Platform Directory Rules, Secret Storage)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/macos.py`
- Create `tests/test_macos_native_support.py`
- Create `tests/fixtures/macos-native-support/env_samples.json`

## Interfaces / Contracts

- `MacOSChecks(env).run() -> list[DoctorCheck]` produces checks named `keychain`, `application_support`, `zsh_shell`, and `gatekeeper_note`.
- Each check uses the shared `DoctorCheck` type and carries a recovery command when failing.
- With `SHELL=/bin/zsh`, `zsh_shell` reports `ok`; Application Support paths follow architecture 09.
- macOS logic never duplicates `app_dirs`/`secrets`; it calls them.

## Data Flow

1. Read the macOS environment (shell, Keychain, paths).
2. Run each macOS-specific check via shared primitives.
3. Mark ok/warn/fail with details.
4. Attach recovery commands to failures.
5. Return the list of `DoctorCheck` records.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_macos_native_support.py::test_zsh_shell_and_application_support_are_checked`**

```python
def test_zsh_shell_and_application_support_are_checked():
    checks = {c.name: c for c in MacOSChecks(env={"SHELL": "/bin/zsh", "HOME": "/Users/u"}).run()}
    assert checks["zsh_shell"].status == "ok"
    assert "Application Support" in checks["application_support"].detail
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_macos_native_support.py::test_zsh_shell_and_application_support_are_checked -q
```

Expected: FAIL because `MacOSChecks` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `MacOSChecks` reusing `app_dirs`, `secrets`, and `platform_io`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_macos_native_support.py::test_zsh_shell_and_application_support_are_checked -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_keychain_unavailable_recommends_env_fallback
test_application_support_paths_match_architecture_matrix
test_non_zsh_shell_is_warned_not_failed
test_gatekeeper_note_present_for_standalone_binary
test_chinese_user_path_round_trips
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_macos_native_support.py -q
pf-agent doctor --section macos
```

Expected: tests pass and the `macos` doctor section reports Keychain, paths, shell, and Gatekeeper notes.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_macos_native_support.py -q
```

Expected: PASS using simulated macOS environments; no real macOS-only API is required to run the tests.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/macos.py tests/test_macos_native_support.py tests/fixtures/macos-native-support
git commit -m "feat: add macos native support"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- macOS checks are driven by a simulated `env` so they test on any host.
- UTF-8 fixtures cover Chinese user paths.
- Shared primitives are reused, not reimplemented.

## Failure Modes To Prove

- Keychain unavailable recommends the env fallback.
- A non-zsh shell is warned, not failed.
- Application Support paths match the architecture matrix.
- Gatekeeper note is present for the standalone binary.

## Verification

```powershell
python -m pytest tests/test_macos_native_support.py -q
pf-agent doctor --section macos
```

## Acceptance

- macOS Keychain, paths, shell, and Gatekeeper checks work.
- The checks reuse shared cross-platform primitives.
- Recovery commands are macOS-appropriate.
- Tests run on any host via simulated environments.

## Commit Boundary

Commit only macOS-support files and tests after verification passes. Do not duplicate shared path/secret logic here.
