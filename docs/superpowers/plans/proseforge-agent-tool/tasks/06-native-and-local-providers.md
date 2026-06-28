# Task 06: Native And Local Provider Profiles

## Goal

Add local and native profile plumbing for Ollama, LM Studio, vLLM, llama.cpp, OpenRouter, and future native adapters.

## Architecture Notes

This creates the extension point for local/gateway profiles while Tasks 18-27 cover named cloud providers.

Read before starting:

- ../architecture/02-system-architecture.md
- ../appendices/01-data-contracts.md
- 00-task-index.md

## Files

- Create `configs/providers.local.example.yaml`
- Create `src/proseforge_agent/llm/profiles.py`
- Create `tests/test_provider_profiles.py`
- Create `tests/fixtures/providers/local_profiles.yaml`

## Interfaces / Contracts

`ProviderProfile` records family, protocol, base URL, model, key env, capabilities, privacy class, and certification level.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_provider_profiles.py::test_local_openai_compatible_profile_loads_without_key`**

```python
def test_local_openai_compatible_profile_loads_without_key(tmp_path):
    path = tmp_path / "providers.yaml"
    path.write_text(
        """providers:
  ollama_main:
    family: ollama
    protocol: local_openai_compatible
    base_url: http://localhost:11434/v1
    model: llama-local
""",
        encoding="utf-8",
    )
    profiles = load_provider_profiles(path)
    assert profiles["ollama_main"].privacy_class == "local"
```

- [ ] **Step 2: Run the targeted test and confirm failure**

Run:

```powershell
python -m pytest tests/test_provider_profiles.py::test_local_openai_compatible_profile_loads_without_key -q
```

Expected: FAIL because `load_provider_profiles` is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement profile schema, capability defaults, local profile examples, and profile validation shared by cloud and local providers.

- [ ] **Step 4: Run the targeted test and confirm pass**

Run:

```powershell
python -m pytest tests/test_provider_profiles.py::test_local_openai_compatible_profile_loads_without_key -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Run integration verification**

Run:

```powershell
python -m pytest tests/test_provider_profiles.py -q
pf-agent provider profiles --config configs/providers.local.example.yaml
```

Expected: command exits 0 and writes only the artifacts named in this card.

- [ ] **Step 6: Record commit boundary**

```powershell
git add configs/providers.local.example.yaml tests
git commit -m "feat: add local provider profiles"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Verification

```powershell
python -m pytest tests/test_provider_profiles.py -q
pf-agent provider profiles --config configs/providers.local.example.yaml
```

## Acceptance

- Local profiles do not require API keys by default.
- Capability fields default to `unknown` unless configured.
- Profile loader rejects missing family, protocol, or model.

## Commit Boundary

Commit after this card passes verification. Do not start the next card with failing tests or unreviewed artifacts from this card.
