# Task 05: OpenAI-Compatible Provider

## Goal

Add the shared transport used by OpenAI-compatible domestic, foreign, local, and gateway providers.

## Architecture Notes

This task adds protocol support, not individual vendor certification. Vendor profiles are added in Tasks 18-27.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/llm/openai_compatible.py`
- Create `src/proseforge_agent/llm/http.py`
- Create `tests/test_openai_compatible_provider.py`
- Create `tests/fixtures/providers/openai_chat_success.json`
- Create `tests/fixtures/providers/openai_chat_error.json`

## Interfaces / Contracts

`OpenAICompatibleProvider` accepts base URL, API key env name, model, timeout, and optional extra body; it maps `/chat/completions` responses into `ProviderResult`.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_openai_compatible_provider.py::test_chat_request_shape_uses_configured_base_url`**

```python
def test_chat_request_shape_uses_configured_base_url(fake_http):
    provider = OpenAICompatibleProvider(name="compat", base_url="https://example.test/v1", api_key="key", model="model-a", http=fake_http)
    provider.generate(ProviderRequest(role="drafter", messages=[Message(role="user", content="Hi")]))
    assert fake_http.requests[0].url == "https://example.test/v1/chat/completions"
    assert fake_http.requests[0].json["model"] == "model-a"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_openai_compatible_provider.py::test_chat_request_shape_uses_configured_base_url -q
```

Expected: FAIL because compatible provider and fake HTTP transport are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement request builder, response parser, streaming parser, fake HTTP test helper, secret-redacted logging hooks, and error normalization for 401, 429, 500, timeout, and malformed JSON.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_openai_compatible_provider.py::test_chat_request_shape_uses_configured_base_url -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_openai_compatible_provider.py -q
pf-agent provider smoke --provider openai-compatible --shape-only
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add src/proseforge_agent/llm/openai_compatible.py tests
git commit -m "feat: add openai compatible provider transport"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_openai_compatible_provider.py -q
pf-agent provider smoke --provider openai-compatible --shape-only
```

## Acceptance

- Base URL and model are config values.
- API keys are never printed in errors.
- Malformed provider payloads become `invalid_response`.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
