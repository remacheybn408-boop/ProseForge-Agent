# Task 117: MCP Server Registry / MCP Server 注册表

## Goal

建立 MCP server 注册表，管理所有外部 MCP server 的配置、启用状态和权限等级。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

新增配置：

```yaml id="m25whj"
mcp:
  servers:
    filesystem:
      enabled: true
      transport: stdio
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
      trust_level: local
```

字段：

* server id
* display name
* transport
* command / url
* env
* working directory
* enabled
* trust level
* permission profile
* timeout
* rate limit

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_server_registry.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-server-registry/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="g2zkw6"
pf-agent mcp add filesystem
pf-agent mcp enable filesystem
pf-agent mcp disable filesystem
pf-agent mcp remove filesystem
pf-agent mcp config filesystem
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_server_registry.py::test_mcp_server_registry_contract`**

```python
def test_mcp_server_registry_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 117 production code is not implemented yet.
    raise AssertionError("Task 117 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_server_registry.py::test_mcp_server_registry_contract -q
```

Expected: FAIL because Task 117 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_server_registry.py::test_mcp_server_registry_contract -q
```

Expected: PASS with the new Task 117 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_server_registry.py
git commit -m "feat: add mcp server registry"
```

## Verification

Source DoD:

用户能通过 CLI 添加、启用、禁用 MCP server，配置持久化保存。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_server_registry.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 117 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_server_registry.py
git commit -m "feat: add mcp server registry"
```

Do not bundle adjacent task cards into this commit.
