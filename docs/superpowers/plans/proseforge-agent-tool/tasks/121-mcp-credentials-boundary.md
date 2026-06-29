# Task 121: MCP Credentials Boundary / MCP 凭证隔离

## Goal

让 MCP server 无法默认读取 ProseForge Agent 的 provider keys、用户 secrets、系统环境变量。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

规则：

* MCP server 默认不继承完整 env。
* 只注入白名单 env。
* secrets 必须显式授权。
* secrets 不进入 logs。
* approval summary 中显示 secret ref，不显示 secret value。

配置：

```yaml id="qfkkjt"
mcp:
  servers:
    github:
      env_allow:
        - "GITHUB_TOKEN"
      secret_refs:
        GITHUB_TOKEN: "keychain://proseforge-agent/github"
```

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_credentials_boundary.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-credentials-boundary/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_credentials_boundary.py::test_mcp_credentials_boundary_contract`**

```python
def test_mcp_credentials_boundary_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 121 production code is not implemented yet.
    raise AssertionError("Task 121 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_credentials_boundary.py::test_mcp_credentials_boundary_contract -q
```

Expected: FAIL because Task 121 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_credentials_boundary.py::test_mcp_credentials_boundary_contract -q
```

Expected: PASS with the new Task 121 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_credentials_boundary.py
git commit -m "feat: add mcp credentials boundary"
```

## Verification

Source DoD:

MCP server 无法读取未授权的 API key。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_credentials_boundary.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 121 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_credentials_boundary.py
git commit -m "feat: add mcp credentials boundary"
```

Do not bundle adjacent task cards into this commit.
