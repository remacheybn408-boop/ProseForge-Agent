# Task 72: Tool Execution Sandbox And Approval Policy

## Goal

Run command/code-execution tools inside a sandbox gated by permission and explicit approval, so an autonomous agent can act without risking the user's system.

## Agent Product Requirement

A complete agent that can run commands must do so safely: confined, time-limited, permission-gated, and only after approval for anything mutating.

> Dependency note: execute after the Tool Registry and Permission Policy (Task 33), the safety guard (Task 62), and the general tool framework (Task 71).

## Architecture Notes

`sandbox` wraps execution-class tools (shell command, code run, mutating engine commands). Execution requires a permission ceiling at or above `engine_write`/`system_write` plus an explicit approval token; the default `read_only` ceiling refuses execution. The sandbox confines the working directory, enforces a timeout, and routes the command through the prompt-injection guard (Task 62) so untrusted-content-driven commands are blocked. It records every execution as an event with a trace id (Task 40). The sandbox does not decide *what* to run; it gates and confines *how* it runs.

Read before starting:

- ../architecture/11-autonomous-agent-runtime.md (Budgets And Safety Guardrails)
- ../architecture/08-agent-runtime-and-chat.md (Permissions)
- ../architecture/02-system-architecture.md
- 00-task-index.md

## Files

- Create `src/proseforge_agent/agent/sandbox.py`
- Create `tests/test_tool_sandbox.py`
- Create `tests/fixtures/tool-execution-sandbox/commands.json`

## Interfaces / Contracts

- `Sandbox(permissions, safety).run(command: ExecRequest, approval: Approval | None) -> ExecResult`.
- `ExecRequest` fields: `argv`, `cwd` (must be inside the workspace), `timeout`; `ExecResult` fields: `ok`, `stdout`, `stderr`, `returncode`, `trace_id`.
- Execution requires a permission ceiling >= the command's declared level AND a valid `approval`; otherwise `ExecResult(ok=False, error="approval required")`.
- The sandbox confines `cwd` to the workspace, enforces `timeout`, and rejects commands flagged by the safety guard.

## Data Flow

1. Receive an execution request and optional approval.
2. Check the permission ceiling and the approval token.
3. Run the safety guard over the command and its source content.
4. Execute confined to the workspace with a timeout.
5. Return a structured `ExecResult` and emit an execution event.

## TDD Steps

- [ ] **Step 1: Write failing unit test `tests/test_tool_sandbox.py::test_command_requires_approval_and_runs_confined`**

```python
def test_command_requires_approval_and_runs_confined(fake_permissions_read_only, fake_safety):
    sandbox = Sandbox(permissions=fake_permissions_read_only, safety=fake_safety)
    denied = sandbox.run(ExecRequest(argv=["echo", "hi"], cwd="."), approval=None)
    assert denied.ok is False  # read_only + no approval
    sandbox2 = Sandbox(permissions=grant("system_write"), safety=fake_safety)
    ok = sandbox2.run(ExecRequest(argv=["echo", "hi"], cwd="."), approval=Approval(confirmed=True))
    assert ok.ok is True
    assert ok.trace_id
```

- [ ] **Step 2: Run the targeted test and confirm failure**

```powershell
python -m pytest tests/test_tool_sandbox.py::test_command_requires_approval_and_runs_confined -q
```

Expected: FAIL because `Sandbox`, `ExecRequest`, `ExecResult`, and `Approval` are missing.

- [ ] **Step 3: Implement the minimum production behavior**

Implement `Sandbox`, `ExecRequest`, `ExecResult`, `Approval`, permission/approval gating, workspace confinement, timeout, and safety routing.

- [ ] **Step 4: Run the targeted test and confirm pass**

```powershell
python -m pytest tests/test_tool_sandbox.py::test_command_requires_approval_and_runs_confined -q
```

Expected: PASS with 1 selected test.

- [ ] **Step 5: Add required companion tests**

```text
test_execution_outside_workspace_cwd_is_rejected
test_timeout_terminates_a_long_running_command
test_safety_guard_blocks_injection_driven_command
test_unapproved_execution_is_refused_with_recovery_message
test_every_execution_emits_event_with_trace_id
```

- [ ] **Step 6: Run subsystem verification**

```powershell
python -m pytest tests/test_tool_sandbox.py -q
pf-agent run --goal "list workspace files" --provider fake --allow-exec --approve
```

Expected: tests pass and execution only proceeds with the elevated permission plus approval.

- [ ] **Step 7: Record commit boundary**

```powershell
git add src/proseforge_agent/agent/sandbox.py tests/test_tool_sandbox.py tests/fixtures/tool-execution-sandbox
git commit -m "feat: add tool execution sandbox and approval policy"
```

If the workspace is not a git repository, record this commit message in the task closeout instead of running git.

## Cross-Platform Notes

- Workspace confinement and timeout work on Windows, macOS, and Linux.
- `argv` is list-form (no shell string interpolation) to avoid quoting bugs.
- Execution events are UTF-8 with relative paths.

## Failure Modes To Prove

- `read_only` ceiling or missing approval refuses execution.
- A `cwd` outside the workspace is rejected.
- A long-running command is terminated at the timeout.
- An injection-driven command is blocked by the safety guard.

## Verification

```powershell
python -m pytest tests/test_tool_sandbox.py -q
pf-agent run --goal "list workspace files" --provider fake --allow-exec --approve
```

## Acceptance

- Execution requires sufficient permission and explicit approval.
- Commands are confined to the workspace and time-limited.
- The safety guard can block dangerous commands.
- Every execution is traced.

## Commit Boundary

Commit only sandbox files and tests after verification passes. Do not broaden the default permission ceiling here.
