# Task 119: MCP Tool Approval Gate / MCP 工具审批门

## Goal

对高风险 MCP 工具调用增加审批机制，接入 Human Approval Queue。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

调用前生成 approval request：

```text id="kahbra"
MCP tool wants to write file:
  server: filesystem
  tool: write_file
  target: drafts/ch_001.md

Approve? [y/N]
```

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_tool_approval_gate.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-tool-approval-gate/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="8yl8qe"
pf-agent approval list
pf-agent approval approve <id>
pf-agent approval reject <id>
```

### Source 高风险动作

* 删除文件
* 覆盖稿件
* 写入 config
* 修改 rules
* 执行 shell command
* 网络请求
* 读取 secrets
* 批量修改项目文件
* 调用未知 MCP tool

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_tool_approval_gate.py::test_mcp_tool_approval_gate_contract`**

```python
def test_mcp_tool_approval_gate_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 119 production code is not implemented yet.
    raise AssertionError("Task 119 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_tool_approval_gate.py::test_mcp_tool_approval_gate_contract -q
```

Expected: FAIL because Task 119 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_tool_approval_gate.py::test_mcp_tool_approval_gate_contract -q
```

Expected: PASS with the new Task 119 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_tool_approval_gate.py
git commit -m "feat: add mcp tool approval gate"
```

## Verification

Source DoD:

危险 MCP 工具默认不能直接执行，必须进入 approval queue。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_tool_approval_gate.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 119 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_tool_approval_gate.py
git commit -m "feat: add mcp tool approval gate"
```

Do not bundle adjacent task cards into this commit.
