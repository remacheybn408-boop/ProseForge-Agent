# Task 197: Enforce MCP Policy In MCPClient.call_tool / MCP 客户端强制策略

## Goal

Make `MCPClient.call_tool` consult `MCPPolicy` (and, when configured, the
`MCPApprovalGate`) **before** executing a tool against the transport. Today the
policy is only reached via `mcp/approval.py`; `MCPClient.call_tool`
(`mcp/client.py:221`) runs any tool name straight through
`self.transport.call_tool(...)` with no policy check. The placeholder transport
masks this in dev, but the moment a real stdio/HTTP transport is wired the
policy is silently absent.

## Architecture Notes

Fixes **finding 1.6** (Critical · Architecture) of
`docs/review/core-review-2026-07-01.md`. Pairs with 202 (loud placeholders):
197 makes the policy enforcing, 202 makes an unwired transport visible.

`grep "MCPPolicy.decide|policy.decide"` finds callers only in
`mcp/approval.py`. The intended flow "client → policy → approval gate →
transport" is broken in the middle.

Design (`src/proseforge_agent/mcp/client.py`):

- `MCPClient.__init__(spec, transport, *, policy: MCPPolicy | None = None,
  approval_gate: MCPApprovalGate | None = None)`.
- In `call_tool`, when `policy` is set:
  1. `decision = policy.decide(tool_name, arguments)` (mirror the fields
     `mcp/approval.py` already uses).
  2. If denied → return `ToolResult(ok=False, error="blocked by MCP policy: …",
     provenance="mcp:<id>")`; do NOT touch the transport.
  3. If approval required and an `approval_gate` is set → enqueue / block on the
     gate's decision; if no gate is set but approval is required, deny with a
     clear "approval required, no gate configured" error.
  4. Only on allow → `self.transport.call_tool(...)`.
- When `policy is None`, behavior is unchanged (back-compat), but the class
  docstring MUST state: *a client constructed without a policy is unsafe for
  production transports.*
- Wire the CLI's `_handle_mcp` construction path so real MCP calls get a policy
  by default.

Read before starting:

- `docs/review/core-review-2026-07-01.md` (finding 1.6, plus 4.1)
- 116-mcp-client-foundation.md … 121-mcp-credential-boundary.md
- `src/proseforge_agent/mcp/{client,policy,approval,credentials}.py`
- `_handle_mcp` in `src/proseforge_agent/cli.py`

## Files

- Modify `src/proseforge_agent/mcp/client.py` (`MCPClient.__init__`,
  `call_tool`, docstring).
- Modify `src/proseforge_agent/cli.py` `_handle_mcp` to pass a policy (+ gate
  where already available).
- Add tests in `tests/test_mcp_policy_enforced_in_client.py`.

## Interfaces / Contracts

- `MCPClient(spec, transport, *, policy=None, approval_gate=None)`.
- Denied tools never reach `transport.call_tool` (assert via a spy transport
  that records calls).
- `policy=None` keeps every existing MCP test green.

## Data Flow

1. Caller builds `MCPClient(spec, transport, policy=policy, approval_gate=gate)`.
2. `call_tool("write_file", {...})` → `policy.decide` → allow/deny/approve.
3. Deny → structured error, transport untouched.
4. Allow → transport executes; result wrapped in `ToolResult`.

## TDD Steps

- [ ] **Step 1: Write failing test
  `tests/test_mcp_policy_enforced_in_client.py::test_call_tool_denied_by_policy_never_touches_transport`**

```python
def test_call_tool_denied_by_policy_never_touches_transport():
    calls = []

    class SpyTransport:
        def call_tool(self, name, arguments):
            calls.append((name, arguments))
            return {"ok": True}

    policy = MCPPolicy(command_allowlist=(), filesystem_allowlist=(), network_allowlist=())
    client = MCPClient(spec, transport=SpyTransport(), policy=policy)

    result = client.call_tool("write_file", {"path": "../../etc/passwd"})

    assert result.ok is False
    assert "policy" in result.error.lower()
    assert calls == []   # transport must NOT run
```

- [ ] **Step 2: Run the targeted test and confirm failure** (today the spy
  records the call because policy is never consulted).

- [ ] **Step 3: Add `policy` / `approval_gate` params and the decide→gate→
  transport flow in `call_tool`; wire the CLI construction path.**

- [ ] **Step 4: Run the targeted test and confirm pass.**

- [ ] **Step 5: Companion tests**

```text
test_call_tool_allowed_by_policy_reaches_transport
test_approval_required_blocks_until_gate_decides
test_approval_required_without_gate_is_denied_clearly
test_client_without_policy_is_backward_compatible
test_cli_handle_mcp_constructs_client_with_policy
```

- [ ] **Step 6: Subsystem verification**

```powershell
python -m pytest tests/test_mcp_policy_enforced_in_client.py tests/test_mcp_*.py -q
```

- [ ] **Step 7: Full repository verification**

```powershell
python -m pytest -q
```

- [ ] **Step 8: Commit boundary**

```powershell
git add src/proseforge_agent/mcp/client.py src/proseforge_agent/cli.py tests/test_mcp_policy_enforced_in_client.py
git commit -m "fix: enforce mcp policy in client call_tool"
```

## Failure Modes To Prove

- A path-escaping `write_file` is denied before the transport runs.
- Approval-required tool with no gate is denied (not silently allowed).
- Existing `default_demo_client` / `StaticMCPTransport` tests unaffected.

## Verification

```powershell
python -m pytest tests/test_mcp_policy_enforced_in_client.py -q
python -m pytest -q
```

## Acceptance

- `MCPClient.call_tool` consults the policy when one is supplied; denied tools
  never reach the transport.
- CLI MCP path constructs the client with a policy.
- Back-compat preserved when `policy=None`; full suite green; new tests added.

## Commit Boundary

Commit only the client policy enforcement, the CLI construction change, and the
new tests. Do not bundle the placeholder-loudness work (202).
