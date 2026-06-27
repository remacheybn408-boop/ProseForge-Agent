# Task 45: Native Secret Storage

## Goal

Store provider keys in Windows Credential Manager, macOS Keychain, Linux Secret Service, or environment fallback.

## Agent Product Requirement

Model provider support must not push users toward plain-text keys.

## Architecture Notes

`SecretStore` abstracts secret get/set over a per-platform backend with an environment-variable fallback. The backend is selected from the platform; when it is unavailable, the store falls back to environment variables and records that the secret is less protected so the doctor (Task 42) can surface it. The store never writes secret values into config, reports, or terminal output. Provider adapters (Task 04+) and the provider setup wizard (Task 46) read keys exclusively through this store.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/09-installation-and-native-platforms.md (Secret Storage)
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/secrets.py`
- Create `tests/test_native_secret_storage.py`
- Create `tests/fixtures/native-secret-storage/backends.json`

## Interfaces / Contracts

- `SecretStore.for_platform(platform: str, backend_available: bool) -> SecretStore`.
- `get(key, env=None) -> SecretLookup`; `SecretLookup` fields: `value`, `backend` (`credential_manager` | `keychain` | `secret_service` | `env_fallback`), `protected` (bool), `warning` (str | None).
- When the native backend is unavailable, `get` uses the environment and sets `backend="env_fallback"`, `protected=False`, and a non-empty `warning`.
- No method returns or logs the secret value in any report or `repr`.

## Data Flow

1. Select the native backend for the platform.
2. Attempt to read the key from the native backend.
3. On unavailability, fall back to the environment variable.
4. Record backend, protected flag, and a fallback warning.
5. Return the `SecretLookup` without exposing the value in logs.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_native_secret_storage.py::test_env_fallback_is_marked_unprotected_with_warning`**

```python
def test_env_fallback_is_marked_unprotected_with_warning():
    store = SecretStore.for_platform("linux", backend_available=False)
    lookup = store.get("OPENAI_API_KEY", env={"OPENAI_API_KEY": "sk-test"})
    assert lookup.value == "sk-test"
    assert lookup.backend == "env_fallback"
    assert lookup.protected is False
    assert lookup.warning
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_native_secret_storage.py::test_env_fallback_is_marked_unprotected_with_warning -q
```

Expected: FAIL because `SecretStore` and `SecretLookup` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `SecretStore`, `SecretLookup`, backend selection, env fallback, and the protected/warning flags.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_native_secret_storage.py::test_env_fallback_is_marked_unprotected_with_warning -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_native_backend_lookup_is_marked_protected
test_secret_value_never_appears_in_repr_or_report
test_missing_key_returns_lookup_with_none_value_and_recovery
test_doctor_secrets_section_reports_backend_in_use
test_secret_keys_support_utf8_project_scoped_names
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_native_secret_storage.py -q
pf-agent doctor --section secrets
```

Expected: command exits 0, reports the active backend, and prints no secret values.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_native_secret_storage.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux backend cases in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/secrets.py tests/test_native_secret_storage.py tests/fixtures/native-secret-storage
git commit -m "feat: add native secret storage"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Simulate Windows Credential Manager, macOS Keychain, and Linux Secret Service in tests.
- Use UTF-8 fixtures with Chinese project-scoped key names.
- Do not require cloud provider keys for local verification.

## Failure Modes To Prove

- Native backend unavailable falls back to env and warns it is unprotected.
- Secret values never appear in `repr`, reports, or terminal output.
- A missing key returns a `None` value plus a recovery message.
- Unknown platform raises `ConfigurationError`.

## Verification

```powershell
python -m pytest tests/test_native_secret_storage.py -q
pf-agent doctor --section secrets
```

## Acceptance

- Keys are read through native backends with a visible env fallback.
- Fallback is marked unprotected and surfaced in the doctor.
- No secret value is ever printed.
- Works in portable and native app-dir modes.

## Commit Boundary

Commit only secret-storage files and tests after verification passes. Do not change provider adapters here.
