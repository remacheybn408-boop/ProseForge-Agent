# Task 118: MCP Security Boundary / MCP 安全边界

## Goal

为 MCP server 增加安全边界，防止外部工具越权访问文件、网络、密钥和项目数据。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

安全维度：

* filesystem allowlist
* filesystem denylist
* network allowlist
* command allowlist
* secret access denied by default
* dangerous tool approval required
* project scope isolation
* read-only mode
* write mode requires approval

配置示例：

```yaml id="9vyjgj"
mcp_security:
  default_policy: restricted
  filesystem:
    allow:
      - "~/.proseforge-agent/workspace"
    deny:
      - "~/.ssh"
      - "~/.config"
      - "~/.proseforge-agent/secrets"
  network:
    allow:
      - "api.deepseek.com"
    deny_all_by_default: true
```

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_security_boundary.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-security-boundary/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

### Source 命令

```bash id="2ew6ls"
pf-agent mcp policy list
pf-agent mcp policy show filesystem
pf-agent mcp policy set filesystem restricted
```

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_security_boundary.py::test_mcp_security_boundary_contract`**

```python
def test_mcp_security_boundary_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 118 production code is not implemented yet.
    raise AssertionError("Task 118 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_security_boundary.py::test_mcp_security_boundary_contract -q
```

Expected: FAIL because Task 118 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_security_boundary.py::test_mcp_security_boundary_contract -q
```

Expected: PASS with the new Task 118 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_security_boundary.py
git commit -m "feat: add mcp security boundary"
```

## Verification

Source DoD:

MCP server 尝试访问 allowlist 外路径时必须被拒绝，并记录 audit log。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_security_boundary.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 118 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_security_boundary.py
git commit -m "feat: add mcp security boundary"
```

Do not bundle adjacent task cards into this commit.
