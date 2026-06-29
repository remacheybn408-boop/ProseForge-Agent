# Task 126: Request Cache / 请求缓存与去重

## Goal

重复请求自动走缓存，减少 token 成本和 provider 调用次数。

## Architecture Notes

This card belongs to the **Resilience And Offline Operation** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

缓存 key 包含：

* prompt hash
* system prompt version
* provider
* model
* evidence pack hash
* tool result hash
* temperature

支持：

```bash id="y8f53s"
pf-agent cache list
pf-agent cache clear
pf-agent cache stats
```

配置：

```yaml id="46bspq"
cache:
  enabled: true
  ttl_seconds: 86400
  scopes:
    - provider_response
    - tool_result
    - evidence_pack
```

## Files

- Create or modify implementation files under `src/proseforge_agent/agent/` as needed for this card.
- Add focused tests in `tests/agent/test_request_cache.py`.
- Add fixtures under `tests/agent/fixtures/request-cache/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/agent/test_request_cache.py::test_request_cache_contract`**

```python
def test_request_cache_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 126 production code is not implemented yet.
    raise AssertionError("Task 126 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/agent/test_request_cache.py::test_request_cache_contract -q
```

Expected: FAIL because Task 126 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/agent/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/agent/test_request_cache.py::test_request_cache_contract -q
```

Expected: PASS with the new Task 126 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/agent/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_request_cache.py
git commit -m "feat: add request cache"
```

## Verification

Source DoD:

相同请求重复执行时，第二次可命中缓存，并在 audit log 中标记 cache hit。

---

Before closing this card, run:

```powershell
python -m pytest tests/agent/test_request_cache.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 126 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/agent/ tests/agent/test_request_cache.py
git commit -m "feat: add request cache"
```

Do not bundle adjacent task cards into this commit.
