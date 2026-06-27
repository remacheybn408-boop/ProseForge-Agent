# Task 20: Provider Profile - Google / Gemini

## Goal

Add Google / Gemini as a first-class model provider with offline shape tests, optional real smoke tests, capability probing, error mapping, and routing acceptance.

## Architecture Notes

Provider implementation must stay behind the normalized provider contract. Model id, base URL, region, endpoint id, and API key names are config values. Workflows must consume `ProviderResult`, never raw Google / Gemini payloads.

Read before starting:

- ../providers/01-normalized-provider-contract.md
- ../providers/05-provider-verification-and-acceptance.md
- ../providers/06-official-source-notes.md
- 05-openai-compatible-provider.md
- 28-provider-capability-probing.md
- 29-provider-fallback-router.md

## Files

- Create `configs/providers/gemini.yaml`
- Create `src/proseforge_agent/llm/providers/gemini.py`
- Modify `src/proseforge_agent/llm/registry.py`
- Create `tests/test_provider_gemini.py`
- Create `tests/fixtures/providers/gemini_success.json`
- Create `tests/fixtures/providers/gemini_error.json`
- Create `tests/fixtures/providers/gemini_stream.txt`

## Interfaces / Contracts

Provider aliases: `gemini, gemini_native, gemini_openai`.

Protocol: GenerateContent plus OpenAI compatibility.

Required environment variable for real smoke: `GEMINI_API_KEY`.

Parser must normalize: candidates, safety feedback, function calls, usage.

Provider certification statuses: `profiled`, `shape_tested`, `smoke_tested`, `workflow_tested`, `certified`.

## TDD Steps

- [ ] **Step 1: Write failing fake transport test `tests/test_provider_gemini.py::test_gemini_request_shape_uses_profile_config`**

```python
def test_gemini_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    profile = load_provider_profiles("configs/providers/gemini.yaml")["gemini_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")]))
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])
```

- [ ] **Step 2: Run the targeted fake transport test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_gemini.py::test_gemini_request_shape_uses_profile_config -q
```

Expected: FAIL because the Google / Gemini profile and provider builder are missing.

- [ ] **Step 3: Implement profile, request builder, and registry alias**

Create `configs/providers/gemini.yaml` with environment-variable model settings, implement `providers/gemini.py`, register aliases `gemini, gemini_native, gemini_openai`, and ensure secrets are redacted from request repr and errors.

- [ ] **Step 4: Add response, stream, and error mapping tests**

Required tests:

```text
test_gemini_parses_success_response_into_provider_result
test_gemini_parses_stream_events_into_normalized_chunks
test_gemini_maps_auth_rate_limit_timeout_and_invalid_response_errors
test_gemini_missing_gemini_api_key_skips_real_smoke
test_gemini_shape_certification_report_records_source_and_checked_date
```

- [ ] **Step 5: Run provider verification**

Run:

```powershell
python -m pytest tests/test_provider_gemini.py -q
pf-agent provider certify --provider gemini --shape-only
pf-agent provider routes --role drafter --provider-family gemini
```

Expected: tests pass, shape certification writes a record, and route report includes Google / Gemini or a clear blocked reason.

- [ ] **Step 6: Add optional real smoke guard**

Run only when the key exists:

```powershell
pf-agent provider certify --provider gemini --real-if-key-present --write-report
```

Expected without key: clean skip mentioning `GEMINI_API_KEY`. Expected with key: one minimal safe prompt, usage captured, no secret values printed.

- [ ] **Step 7: Record commit boundary**

```powershell
git add configs/providers/gemini.yaml src/proseforge_agent/llm tests/fixtures/providers tests/test_provider_gemini.py
git commit -m "feat: add gemini provider profile"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_gemini.py -q
pf-agent provider certify --provider gemini --shape-only
pf-agent provider routes --role drafter --provider-family gemini
```

## Acceptance

- Google / Gemini appears in provider status and route reports.
- Fake transport tests cover request shape, success response, stream events, and normalized errors.
- Shape certification works without `GEMINI_API_KEY`.
- Optional real smoke is gated by `GEMINI_API_KEY` and never prints secrets.
- Capability probing records supported, unsupported, and unverified capabilities.
- Workflow code uses normalized `ProviderResult` only.

## Commit Boundary

Commit after provider tests, shape certification, and route report all pass. Do not call this provider `certified` until certification records meet the levels in ../providers/05-provider-verification-and-acceptance.md.
