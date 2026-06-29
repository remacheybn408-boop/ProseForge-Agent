# Task 116: MCP Client Foundation / MCP 客户端基础

## Goal

为 ProseForge Agent 增加 MCP client 基础能力，使 agent 可以连接外部 MCP server，并读取其暴露的 tools/resources/prompts。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

支持：

* stdio MCP server
* HTTP/SSE MCP server 预留
* MCP server 启动与关闭
* server capability discovery
* tools list
* resources list
* prompts list
* MCP 调用结果转换为内部 ToolResult

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_client_foundation.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-client-foundation/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="mu5m4b"
pf-agent mcp list
pf-agent mcp inspect <server>
pf-agent mcp tools <server>
pf-agent mcp resources <server>
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_client_foundation.py::test_mcp_client_foundation_contract`**

```python
def test_mcp_client_foundation_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 116 production code is not implemented yet.
    raise AssertionError("Task 116 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_client_foundation.py::test_mcp_client_foundation_contract -q
```

Expected: FAIL because Task 116 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_client_foundation.py::test_mcp_client_foundation_contract -q
```

Expected: PASS with the new Task 116 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_client_foundation.py
git commit -m "feat: add mcp client foundation"
```

## Verification

Source DoD:

配置一个本地 MCP server 后：

```bash id="2fxb66"
pf-agent mcp inspect filesystem
```

能列出 server capabilities、tools、resources。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_client_foundation.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 116 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_client_foundation.py
git commit -m "feat: add mcp client foundation"
```

Do not bundle adjacent task cards into this commit.
