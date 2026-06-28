# Task 71: General Tool Framework And Filesystem/Web Tools

## Goal

Extend the tool registry with general-purpose tools — filesystem read/write/edit confined to the workspace, and web fetch/search behind permission — so the agent can act beyond domain commands.

## Agent Product Requirement

A complete agent reads and writes files and gathers information from the web, not only calls domain functions. These tools must be safe by construction.

> Dependency note: execute after the Tool Registry and Permission Policy (Task 33). Filesystem tools reuse the workspace path containment from Task 02; untrusted tool output flows through the safety guard (Task 62).

## Architecture Notes

This extends `agent/tools.py` (Task 33) with a general tool category. Filesystem tools (`fs.read` / `fs.write` / `fs.edit`) resolve every path through the workspace path builder and **must not escape the workspace** (reuses the `safe_slug`/containment rule). Web tools (`web.fetch` / `web.search`) require an explicit network permission and an injected HTTP client so tests stay offline. A tool returns a structured result (never raises into the loop), and tool *output* is treated as untrusted content for the safety guard (Task 62). Mutating/executing tools are gated by the sandbox (Task 72), not this card.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Module Map)
- ../architecture/08-agent-runtime-and-chat.md (Tool Registry And Permissions)
- ../architecture/02-system-architecture.md (Dependency Direction)
- 00-task-index.md

## Files

- Modify `src/proseforge_agent/agent/tools.py`
- Create `src/proseforge_agent/agent/tools_fs.py`
- Create `src/proseforge_agent/agent/tools_web.py`
- Create `tests/test_general_tools.py`
- Create `tests/fixtures/general-tool-framework/workspace_seed/`

## Interfaces / Contracts

- General tools register under names `fs.read`, `fs.write`, `fs.edit`, `web.fetch`, `web.search` with a declared minimum permission level.
- `Tool.invoke(args, ctx) -> ToolResult`; `ToolResult` fields: `ok`, `output`, `error`, `provenance` (`untrusted` for external content).
- Filesystem tools resolve paths inside `workspace_root`; a path that escapes raises `ConfigurationError` before any IO.
- Web tools require the network permission and use the injected HTTP client; without permission they return `ToolResult(ok=False, error=...)`.

## Data Flow

1. The loop/kernel requests a tool by name with args.
2. The registry checks the tool's minimum permission against the current ceiling.
3. Filesystem tools resolve and containment-check the path; web tools check network permission.
4. The tool runs and returns a structured `ToolResult`.
5. External output is tagged `untrusted` for the safety guard.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_general_tools.py::test_fs_write_tool_is_confined_to_workspace`**

```python
def test_fs_write_tool_is_confined_to_workspace(tmp_workspace):
    fs_write = tool_registry.get("fs.write")
    with pytest.raises(ConfigurationError):
        fs_write.invoke({"path": "../escape.txt", "content": "x"}, ctx=tmp_workspace)
    ok = fs_write.invoke({"path": "notes/a.txt", "content": "x"}, ctx=tmp_workspace)
    assert ok.ok is True
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_general_tools.py::test_fs_write_tool_is_confined_to_workspace -q
```

Expected: FAIL because the general tools are not registered yet.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `tools_fs.py`, `tools_web.py`, registration in `tools.py`, `ToolResult`, path containment, and permission gating.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_general_tools.py::test_fs_write_tool_is_confined_to_workspace -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_fs_read_returns_untrusted_provenance_for_file_content
test_web_fetch_requires_network_permission
test_web_tools_use_injected_http_client_only
test_tool_error_returns_structured_result_not_exception
test_fs_tools_handle_utf8_and_spaces_in_paths
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_general_tools.py -q
pf-agent tools list
```

Expected: tests pass and `tools list` shows the general tools with their required permission levels.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/tools.py src/proseforge_agent/agent/tools_fs.py src/proseforge_agent/agent/tools_web.py tests/test_general_tools.py tests/fixtures/general-tool-framework
git commit -m "feat: add general tool framework with fs and web tools"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Filesystem tools resolve UTF-8 paths and paths with spaces within the workspace.
- Web tools use an injected HTTP client; tests never hit the network.
- Path containment works on Windows, macOS, and Linux.

## Failure Modes To Prove

- A filesystem path escaping the workspace raises before any IO.
- File content is tagged `untrusted` for the safety guard.
- Web tools without network permission return a structured refusal.
- A tool error becomes a `ToolResult`, never an exception into the loop.

## Verification

```powershell
python -m pytest tests/test_general_tools.py -q
pf-agent tools list
```

## Acceptance

- General fs/web tools are registered with permission levels.
- Filesystem tools cannot escape the workspace.
- Web tools require network permission and an injected client.
- Tool output provenance feeds the safety guard.

## Commit Boundary

Commit only the tool framework files and tests after verification passes. Command/code execution and its sandbox belong to Task 72.
