# Task 120: MCP Tool Schema Validation / MCP 工具 Schema 校验

## Goal

对 MCP tools 的输入输出 schema 进行严格校验，避免坏参数、注入参数、越权参数进入工具。

## Architecture Notes

This card belongs to the **MCP Integration** track. Keep the implementation focused in the existing ProseForge Agent architecture and reuse established CLI, report, config, permission, and persistence patterns where they already exist.

### Source Core Requirements

能力：

* tool input schema validation
* tool output validation
* unknown field reject
* path normalization
* path traversal detection
* JSON schema error report
* schema version cache

## Files

- Create or modify implementation files under `src/proseforge_agent/mcp/` as needed for this card.
- Add focused tests in `tests/mcp/test_mcp_tool_schema_validation.py`.
- Add fixtures under `tests/mcp/fixtures/mcp-tool-schema-validation/` only when deterministic sample data is needed.
- Update CLI/report wiring only if the source card explicitly requires a command or user-visible surface.

## Interfaces / Contracts

No extra CLI/API surface was specified in the source card. Preserve existing command style and add only the minimum interface required by the goal.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/mcp/test_mcp_tool_schema_validation.py::test_mcp_tool_schema_validation_contract`**

```python
def test_mcp_tool_schema_validation_contract():
    # Replace this scaffold with the concrete assertion from the card goal.
    # The first run must fail because Task 120 production code is not implemented yet.
    raise AssertionError("Task 120 contract not implemented")
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/mcp/test_mcp_tool_schema_validation.py::test_mcp_tool_schema_validation_contract -q
```

Expected: FAIL because Task 120 production behavior is missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement the smallest cohesive change under `src/proseforge_agent/mcp/` that satisfies the source requirements and keeps unrelated subsystems unchanged.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/mcp/test_mcp_tool_schema_validation.py::test_mcp_tool_schema_validation_contract -q
```

Expected: PASS with the new Task 120 behavior covered.

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
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_tool_schema_validation.py
git commit -m "feat: add mcp tool schema validation"
```

## Verification

Source DoD:

传入非法参数时，MCP tool 不会执行，并返回结构化错误。

---

Before closing this card, run:

```powershell
python -m pytest tests/mcp/test_mcp_tool_schema_validation.py -q
python -m pytest -q
```

## Acceptance

- The behavior described in the source goal is implemented and covered by tests.
- Any command/API/config surface named in the source card works through the existing project conventions.
- The implementation is deterministic in tests and does not require real network/provider credentials unless the card explicitly says so.
- Existing user data, project artifacts, secrets, and config are preserved unless this card explicitly requires a safe migration or backup.

## Commit Boundary

Commit only Task 120 implementation files, tests, and required fixtures:

```powershell
git add src/proseforge_agent/mcp/ tests/mcp/test_mcp_tool_schema_validation.py
git commit -m "feat: add mcp tool schema validation"
```

Do not bundle adjacent task cards into this commit.
