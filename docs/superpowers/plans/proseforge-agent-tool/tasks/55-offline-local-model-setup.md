# Task 55: Offline Local Model Setup

## Goal

Guide setup for Ollama, LM Studio, vLLM, llama.cpp, and local OpenAI-compatible servers.

## Agent Product Requirement

Complete agent support includes local and offline models, not just cloud APIs.

## Architecture Notes

`local_models` detects local OpenAI-compatible endpoints and turns them into provider profile candidates marked as private/offline. Detection uses an injected HTTP client so tests never touch the network. Local models are configured through the same `openai_compatible` profile shape used by cloud providers (Task 05); this card adds discovery and a privacy flag, not a new provider adapter. It reuses the provider matrix and `SecretStore` (Task 45) when a local server requires a token.

Read before starting:

- ../architecture/02-system-architecture.md
- ../architecture/05-model-provider-adapters.md
- ../architecture/09-installation-and-native-platforms.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/install/local_models.py`
- Create `tests/test_offline_local_model_setup.py`
- Create `tests/fixtures/offline-local-model-setup/models_response.json`

## Interfaces / Contracts

- `LocalModelDetector(http).detect(endpoints=None) -> list[LocalModelCandidate]`.
- `LocalModelCandidate` fields: `endpoint`, `models`, `privacy` (`local`), `profile_shape` (`openai_compatible`).
- Detection probes well-known local ports (e.g. Ollama, LM Studio, vLLM) through the injected HTTP client only.
- A reachable endpoint yields candidates with `privacy="local"`; an unreachable one is skipped with a note, not an exception.

## Data Flow

1. Build the candidate endpoint list (defaults + user-supplied).
2. Probe each endpoint's model list via the injected HTTP client.
3. Build `openai_compatible` profile candidates for reachable endpoints.
4. Mark candidates as `privacy="local"`.
5. Return the candidate list and a discovery report.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_offline_local_model_setup.py::test_reachable_local_endpoint_yields_openai_compatible_candidate`**

```python
def test_reachable_local_endpoint_yields_openai_compatible_candidate(fake_http):
    candidates = LocalModelDetector(fake_http).detect(endpoints=["http://localhost:11434/v1"])
    assert candidates
    cand = candidates[0]
    assert cand.privacy == "local"
    assert cand.profile_shape == "openai_compatible"
    assert cand.models
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_offline_local_model_setup.py::test_reachable_local_endpoint_yields_openai_compatible_candidate -q
```

Expected: FAIL because `LocalModelDetector` and `LocalModelCandidate` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `LocalModelDetector`, `LocalModelCandidate`, endpoint probing, and candidate building.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_offline_local_model_setup.py::test_reachable_local_endpoint_yields_openai_compatible_candidate -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_unreachable_endpoint_is_skipped_with_note_not_exception
test_candidate_profile_reuses_openai_compatible_shape
test_local_server_token_is_stored_through_secret_store
test_detection_uses_injected_http_only
test_chinese_model_display_names_round_trip
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_offline_local_model_setup.py -q
pf-agent provider discover-local
```

Expected: tests pass and the command lists reachable local endpoints as provider candidates.

- [ ] **Step 7: Run cross-platform contract check**

```powershell
python -m pytest tests/test_offline_local_model_setup.py -q
```

Expected: PASS with the injected HTTP client on Windows, macOS, and Linux.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/install/local_models.py tests/test_offline_local_model_setup.py tests/fixtures/offline-local-model-setup
git commit -m "feat: add offline local model setup"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Detection uses an injected HTTP client; tests never hit the network.
- Endpoints are URLs, not filesystem paths.
- UTF-8 fixtures cover Chinese model display names.

## Failure Modes To Prove

- An unreachable endpoint is skipped with a note, not an exception.
- A local server token is stored through `SecretStore`, never in plain config.
- Detection performs no real network call in tests.
- Local candidates are clearly marked private.

## Verification

```powershell
python -m pytest tests/test_offline_local_model_setup.py -q
pf-agent provider discover-local
```

## Acceptance

- Local OpenAI-compatible endpoints become provider candidates.
- Candidates reuse the `openai_compatible` profile shape.
- Local models are marked private.
- Tokens go through `SecretStore`.

## Commit Boundary

Commit only local-model files and tests after verification passes. Do not add a new provider adapter here.
