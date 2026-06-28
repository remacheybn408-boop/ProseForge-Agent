# Task 33: Tool Registry And Permission Policy

## Goal

Create the internal tool registry and permission gates that make chat-driven actions safe.

## Agent Product Requirement

Users should be able to chat freely without accidentally mutating projects, accepting chapters, changing secrets, installing shell integration, or writing to the ProseForge engine.

## Architecture Notes

Tools are named internal actions. The Agent Kernel checks permission policy before invoking them. Tool implementation details stay outside chat UI.

## Files

- Create `src/proseforge_agent/agent/tools.py`
- Create `src/proseforge_agent/agent/permissions.py`
- Create `tests/test_agent_tools_permissions.py`
- Create `tests/fixtures/agent/tool_registry.yaml`

## Interfaces / Contracts

- Permission levels: `read_only`, `draft_write`, `project_write`, `engine_write`, `system_write`.
- `AgentTool(name, permission, input_schema, output_schema, callable)`.
- `PermissionDecision(status, reason, required_permission, confirmation_prompt)`.
- `PermissionPolicy.authorize(tool_name, permission_level, session_context)`.

## Data Flow

1. Register built-in tools at startup.
2. Resolve target tool from intent decision.
3. Compare tool permission with session permission ceiling.
4. Return allow, deny, or confirm_required.
5. Invoke tool only after allow.
6. Record audit event for every allow, deny, or confirmation.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_agent_tools_permissions.py::test_read_only_session_cannot_run_project_write_tool`**

```python
def test_read_only_session_cannot_run_project_write_tool():
    registry = ToolRegistry()
    registry.register(
        AgentTool(
            name="chapter.accept",
            permission="project_write",
            input_schema={},
            output_schema={},
            callable=lambda payload: {"ok": True},
        )
    )
    decision = PermissionPolicy().authorize("chapter.accept", permission_level="read_only", registry=registry)
    assert decision.status == "denied"
    assert "project_write" in decision.reason
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_agent_tools_permissions.py::test_read_only_session_cannot_run_project_write_tool -q
```

Expected: FAIL because `ToolRegistry`, `AgentTool`, and `PermissionPolicy` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement tool registration, duplicate-name rejection, permission ordering, policy decisions, confirmation prompts, and audit payloads.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_agent_tools_permissions.py::test_read_only_session_cannot_run_project_write_tool -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

Required tests:

```text
test_duplicate_tool_name_is_rejected
test_draft_write_allows_chapter_draft_but_not_accept
test_system_write_requires_explicit_confirm
test_tool_invocation_records_audit_event
test_unknown_tool_returns_controlled_denial
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_agent_tools_permissions.py -q
pf-agent tools list --include-permissions
```

Expected: command exits 0 and lists tool name, permission, description, and enabled status.

## Cross-Platform Notes

- Tool names use dot notation, never path separators.
- System-write tools are disabled in non-interactive CI unless explicitly enabled.
- Audit events store portable metadata instead of shell-specific raw command lines.

## Failure Modes To Prove

- Unknown tool name returns a denial result.
- Permission denial never calls the callable.
- Schema mismatch is reported before execution.
- System-write confirmation expires after one turn unless accepted.

## Verification

```powershell
python -m pytest tests/test_agent_tools_permissions.py -q
pf-agent tools list --include-permissions
```

## Acceptance

- Every built-in tool declares a permission level.
- Read-only chat cannot mutate project state.
- System installation actions require explicit confirmation.
- Tool calls create audit events.
- The kernel can use the registry without importing workflow internals.

## Commit Boundary

Commit permission and tool registry files only after verification passes.
