# Task 04: Provider Contracts And Fake Provider

## Goal

Create the normalized provider contract, registry, and deterministic fake provider.

## Architecture Notes

Every workflow must run offline through the fake provider before real model APIs are introduced.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `configs/providers.example.yaml`
- Create `src/proseforge_agent/llm/base.py`
- Create `src/proseforge_agent/llm/fake.py`
- Create `src/proseforge_agent/llm/registry.py`
- Create `tests/test_provider_registry.py`
- Create `tests/test_llm_fake_and_routing.py`

## Interfaces / Contracts

`ProviderRequest`, `ProviderResult`, `ProviderError`, `LLMProvider`, `ProviderSpec`, and `ProviderRegistry.provider_for_role(role)` are the only workflow-facing provider APIs.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_llm_fake_and_routing.py::test_fake_provider_returns_deterministic_result`**

```python
def test_fake_provider_returns_deterministic_result():
    provider = FakeProvider(name="fake_main", model="fake-novelist")
    result = provider.generate(ProviderRequest(role="drafter", messages=[Message(role="user", content="chapter")]))
    assert result.provider == "fake_main"
    assert "fake-novelist" in result.text
    assert result.usage.total_tokens >= 0
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_llm_fake_and_routing.py::test_fake_provider_returns_deterministic_result -q
```

Expected: FAIL because `FakeProvider` and provider dataclasses are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement provider dataclasses, fake generation, fake streaming chunks, YAML registry loading, role fallback, and normalized provider errors.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_llm_fake_and_routing.py::test_fake_provider_returns_deterministic_result -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_provider_registry.py tests/test_llm_fake_and_routing.py -q
pf-agent provider smoke --provider fake
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add configs/providers.example.yaml tests
git commit -m "feat: add provider contract and fake provider"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_registry.py tests/test_llm_fake_and_routing.py -q
pf-agent provider smoke --provider fake
```

## Acceptance

- No network or API key is required.
- Registry resolves planner, drafter, critic, reviser, and memory roles.
- Unknown provider names raise `ConfigurationError` with the provider name.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
