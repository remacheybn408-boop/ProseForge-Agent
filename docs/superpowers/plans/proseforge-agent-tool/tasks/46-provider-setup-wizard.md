# Task 46: Provider Setup Wizard

## Goal

Guide users through setting up domestic, foreign, local, and gateway providers.

## Agent Product Requirement

Provider setup should be conversational and cross-platform, not hand-editing YAML from memory.

## Architecture Notes

`ProviderSetupWizard` writes a provider profile into config and stores the API key through `SecretStore` (Task 45). The key value is never written into the profile or any report; the profile holds only a secret reference. It uses the provider matrices (providers docs) to know which providers are OpenAI-compatible vs native. It performs no live provider call during setup unless an explicit `--verify` is requested, which routes through the normalized provider contract (Task 04).

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/05-model-provider-adapters.md
- ../architecture/09-installation-and-native-platforms.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/provider_setup.py`
- Create `tests/test_provider_setup_wizard.py`
- Create `tests/fixtures/provider-setup-wizard/expected_profile.yaml`

## Interfaces / Contracts

- `ProviderSetupWizard(root, secret_store).configure(provider, api_key, model) -> ProviderSetupResult`.
- `ProviderSetupResult` fields: `profile_path`, `secret_ref`, `provider`, `model`, `verified` (bool).
- The written profile contains a `secret_ref`, never the raw `api_key`.
- The key is stored through `SecretStore`; setup does not print or log it.

## Data Flow

1. Resolve the provider entry from the provider matrix.
2. Store the API key through `SecretStore` and obtain a secret reference.
3. Write the provider profile with the secret reference and model.
4. Optionally verify the provider through the normalized contract.
5. Return `ProviderSetupResult` with artifact paths.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_setup_wizard.py::test_setup_writes_profile_with_secret_ref_not_raw_key`**

```python
def test_setup_writes_profile_with_secret_ref_not_raw_key(tmp_path, fake_secret_store):
    wizard = ProviderSetupWizard(tmp_path, fake_secret_store)
    result = wizard.configure(provider="deepseek", api_key="sk-secret", model="deepseek-chat")
    profile_text = result.profile_path.read_text(encoding="utf-8")
    assert "sk-secret" not in profile_text
    assert result.secret_ref in profile_text
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_provider_setup_wizard.py::test_setup_writes_profile_with_secret_ref_not_raw_key -q
```

Expected: FAIL because `ProviderSetupWizard` and `ProviderSetupResult` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `ProviderSetupWizard`, `ProviderSetupResult`, secret storage via `SecretStore`, and profile writing.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_provider_setup_wizard.py::test_setup_writes_profile_with_secret_ref_not_raw_key -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_openai_compatible_provider_uses_compatible_profile_shape
test_native_provider_uses_native_profile_shape
test_verify_flag_routes_through_normalized_contract
test_unknown_provider_raises_configuration_error
test_profile_supports_utf8_provider_display_names
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_provider_setup_wizard.py -q
pf-agent provider setup --provider deepseek --model deepseek-chat
```

Expected: command exits 0, writes a profile with a secret reference, and prints no key value.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_provider_setup_wizard.py -q
```

Expected: PASS for simulated Windows, macOS, and Linux secret backends in the test file.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/provider_setup.py tests/test_provider_setup_wizard.py tests/fixtures/provider-setup-wizard
git commit -m "feat: add provider setup wizard"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Secrets go through the native `SecretStore` with env fallback.
- Profiles use relative/env paths, never absolute machine paths.
- UTF-8 fixtures cover Chinese provider display names.

## Failure Modes To Prove

- The raw API key never appears in the profile or any report.
- Unknown provider raises `ConfigurationError`.
- `--verify` failure reports a recovery command, not a stack trace.
- Missing config produces a recovery command.

## Verification

```powershell
python -m pytest tests/test_provider_setup_wizard.py -q
pf-agent provider setup --provider deepseek --model deepseek-chat
```

## Acceptance

- Provider profiles are written with secret references only.
- Keys are stored through `SecretStore`.
- OpenAI-compatible and native providers use the correct profile shape.
- Optional verify routes through the normalized contract.

## Commit Boundary

Commit only provider-setup files and tests after verification passes. Do not modify provider adapters here.
