# Task 51: Linux Native Support

## Goal

Make Linux a first-class runtime for install, chat, provider setup, and writing workflows.

## Agent Product Requirement

Linux users expect XDG paths, bash/zsh/fish completions, headless operation, and local model servers.

## Architecture Notes

`linux` contributes the Linux-specific check group used by the doctor (Task 42) and reuses `platform_io` (Task 44), `app_dirs` (Task 43), and `secrets` (Task 45). It checks XDG directory resolution, Secret Service (libsecret) availability with env fallback, terminal UTF-8, and notes for a systemd user service and local model endpoints. Linux-only logic lives here; shared primitives are called, not copied.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Cross-Platform Directory Rules, Secret Storage)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/linux.py`
- Create `tests/test_linux_native_support.py`
- Create `tests/fixtures/linux-native-support/env_samples.json`

## Interfaces / Contracts

- `LinuxChecks(env).run() -> list[DoctorCheck]` produces checks named `xdg_dirs`, `secret_service`, `terminal_utf8`, and `systemd_user_service`.
- Each check uses the shared `DoctorCheck` type and carries a recovery command when failing.
- With `XDG_CONFIG_HOME` set, `xdg_dirs` reports `ok` and resolves under that path; Secret Service unavailable falls back to env with a warning.
- Linux logic never duplicates `app_dirs`/`secrets`; it calls them.

## Data Flow

1. Read the Linux environment (XDG vars, shell, secret backend).
2. Run each Linux-specific check via shared primitives.
3. Mark ok/warn/fail with details.
4. Attach recovery commands to failures.
5. Return the list of `DoctorCheck` records.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_linux_native_support.py::test_xdg_config_home_is_honoured_and_secret_service_checked`**

```python
def test_xdg_config_home_is_honoured_and_secret_service_checked():
    checks = {c.name: c for c in LinuxChecks(env={"XDG_CONFIG_HOME": "/tmp/cfg"}).run()}
    assert checks["xdg_dirs"].status == "ok"
    assert "secret_service" in checks
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_linux_native_support.py::test_xdg_config_home_is_honoured_and_secret_service_checked -q
```

Expected: FAIL because `LinuxChecks` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `LinuxChecks` reusing `app_dirs`, `secrets`, and `platform_io`.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_linux_native_support.py::test_xdg_config_home_is_honoured_and_secret_service_checked -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_secret_service_unavailable_recommends_env_fallback
test_xdg_fallback_used_when_vars_unset
test_terminal_utf8_check_reports_capability
test_systemd_user_service_note_is_present
test_chinese_home_path_round_trips
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_linux_native_support.py -q
pf-agent doctor --section linux
```

Expected: tests pass and the `linux` doctor section reports XDG, secret service, and terminal checks.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_linux_native_support.py -q
```

Expected: PASS using simulated Linux environments; no real libsecret is required to run the tests.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/linux.py tests/test_linux_native_support.py tests/fixtures/linux-native-support
git commit -m "feat: add linux native support"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Linux checks are driven by a simulated `env` so they test on any host.
- UTF-8 fixtures cover Chinese home paths.
- Shared primitives are reused, not reimplemented.

## Failure Modes To Prove

- Secret Service unavailable recommends the env fallback.
- XDG vars unset fall back to documented defaults.
- Terminal without UTF-8 is reported with a recovery note.
- Headless operation needs no GUI dependency.

## Verification

```powershell
python -m pytest tests/test_linux_native_support.py -q
pf-agent doctor --section linux
```

## Acceptance

- Linux XDG, secret service, and terminal checks work.
- The checks reuse shared cross-platform primitives.
- Recovery commands are Linux-appropriate.
- Tests run on any host via simulated environments.

## Commit Boundary

Commit only Linux-support files and tests after verification passes. Do not duplicate shared path/secret logic here.
