# Task 19: Provider Profile - Anthropic / Claude

## Goal

Add Anthropic / Claude as a first-class model provider with offline shape tests, optional real smoke tests, capability probing, error mapping, and routing acceptance.

## Architecture Notes

Provider implementation must stay behind the normalized provider contract. Model id, base URL, region, endpoint id, and API key names are config values. Workflows must consume `ProviderResult`, never raw Anthropic / Claude payloads.

Read before starting:

- ../providers/01-normalized-provider-contract.md
- ../providers/05-provider-verification-and-acceptance.md
- ../providers/06-official-source-notes.md
- 05-openai-compatible-provider.md
- 28-provider-capability-probing.md
- 29-provider-fallback-router.md

## Files

- Create `configs/providers/anthropic.yaml`
- Create `src/proseforge_agent/llm/providers/anthropic.py`
- Modify `src/proseforge_agent/llm/registry.py`
- Create `tests/test_provider_anthropic.py`
- Create `tests/fixtures/providers/anthropic_success.json`
- Create `tests/fixtures/providers/anthropic_error.json`
- Create `tests/fixtures/providers/anthropic_stream.txt`

## Interfaces / Contracts

Provider aliases: `anthropic, claude`.

Protocol: Anthropic Messages API.

Required environment variable for real smoke: `ANTHROPIC_API_KEY`.

Parser must normalize: content blocks, tool-use blocks, stop reasons, usage.

Provider certification statuses: `profiled`, `shape_tested`, `smoke_tested`, `workflow_tested`, `certified`.

## TDD Steps

- [ ] **Step 1: Write failing fake transport test `tests/test_provider_anthropic.py::test_anthropic_request_shape_uses_profile_config`**

```python
def test_anthropic_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    profile = load_provider_profiles("configs/providers/anthropic.yaml")["anthropic_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")]))
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])
```

- [ ] **Step 2: Run the targeted fake transport test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_anthropic.py::test_anthropic_request_shape_uses_profile_config -q
```

Expected: FAIL because the Anthropic / Claude profile and provider builder are missing.

- [ ] **Step 3: Implement profile, request builder, and registry alias**

Create `configs/providers/anthropic.yaml` with environment-variable model settings, implement `providers/anthropic.py`, register aliases `anthropic, claude`, and ensure secrets are redacted from request repr and errors.

- [ ] **Step 4: Add response, stream, and error mapping tests**

Required tests:

```text
test_anthropic_parses_success_response_into_provider_result
test_anthropic_parses_stream_events_into_normalized_chunks
test_anthropic_maps_auth_rate_limit_timeout_and_invalid_response_errors
test_anthropic_missing_anthropic_api_key_skips_real_smoke
test_anthropic_shape_certification_report_records_source_and_checked_date
```

- [ ] **Step 5: Run provider verification**

Run:

```powershell
python -m pytest tests/test_provider_anthropic.py -q
pf-agent provider certify --provider anthropic --shape-only
pf-agent provider routes --role drafter --provider-family anthropic
```

Expected: tests pass, shape certification writes a record, and route report includes Anthropic / Claude or a clear blocked reason.

- [ ] **Step 6: Add optional real smoke guard**

Run only when the key exists:

```powershell
pf-agent provider certify --provider anthropic --real-if-key-present --write-report
```

Expected without key: clean skip mentioning `ANTHROPIC_API_KEY`. Expected with key: one minimal safe prompt, usage captured, no secret values printed.

- [ ] **Step 7: Record commit boundary**

```powershell
git add configs/providers/anthropic.yaml src/proseforge_agent/llm tests/fixtures/providers tests/test_provider_anthropic.py
git commit -m "feat: add anthropic provider profile"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_anthropic.py -q
pf-agent provider certify --provider anthropic --shape-only
pf-agent provider routes --role drafter --provider-family anthropic
```

## Acceptance

- Anthropic / Claude appears in provider status and route reports.
- Fake transport tests cover request shape, success response, stream events, and normalized errors.
- Shape certification works without `ANTHROPIC_API_KEY`.
- Optional real smoke is gated by `ANTHROPIC_API_KEY` and never prints secrets.
- Capability probing records supported, unsupported, and unverified capabilities.
- Workflow code uses normalized `ProviderResult` only.

## Commit Boundary

Commit after provider tests, shape certification, and route report all pass. Do not call this provider `certified` until certification records meet the levels in ../providers/05-provider-verification-and-acceptance.md.
