# Task 122: Tool Timeout / Rate Limit / Circuit Breaker

## Goal

给所有工具调用增加超时、限流、熔断能力，防止 agent 被工具卡死。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

适用范围：

* built-in tools
* writing domain tools
* MCP tools
* external web tools
* provider calls

能力：

* per-tool timeout
* per-server timeout
* retry policy
* exponential backoff
* rate limit
* circuit breaker
* failure counter

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py`.
- Add fixtures under `tests/mcp/fixtures/tool-timeout-and-rate-limit-and-circuit-breaker/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 配置

```yaml id="d3jlbi"
tool_runtime:
  default_timeout_seconds: 30
  max_retries: 2
  circuit_breaker:
    failure_threshold: 5
    cooldown_seconds: 300
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py::test_tool_timeout_and_rate_limit_and_circuit_breaker_contract`**

```python
def test_tool_timeout_and_rate_limit_and_circuit_breaker_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 122 production code is not implemented yet.
    raise AssertionError("Task 122 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py::test_tool_timeout_and_rate_limit_and_circuit_breaker_contract -q
```

Expected: FAIL because Task 122 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py::test_tool_timeout_and_rate_limit_and_circuit_breaker_contract -q
```

Expected: PASS with the new Task 122 behavior covered.

- [ ] **Step 5: Add companion tests for the source DoD and failure modes**

Cover all command/API/config behaviors named in this card, including non-destructive behavior, no-secret-leak behavior, permission checks, degraded/offline behavior, or deterministic fake-provider behavior when relevant.

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/mcp/ -q
```

Expected: subsystem tests pass.

- [ ] **Step 7: Run full repository verification**

```powershell
python -m pytest -q
```

Expected: full suite passes.

- [ ] **Step 8: Record commit boundary**

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py
git commit -m "feat: add tool timeout and rate limit and circuit breaker"
```

## Verification

Source DoD:

工具连续失败超过阈值后，短时间内不再调用，并输出降级提示。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 122 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_tool_timeout_and_rate_limit_and_circuit_breaker.py
git commit -m "feat: add tool timeout and rate limit and circuit breaker"
```

Do not bundle adjacent task cards into this commit.
