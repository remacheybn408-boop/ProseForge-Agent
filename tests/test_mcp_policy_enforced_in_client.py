"""MCP policy enforced inside MCPClient.call_tool (Task 197, finding 1.6)."""

from __future__ import annotations

import pytest

from proseforge_agent.mcp.approval import MCPApprovalGate, MCPApprovalQueue
from proseforge_agent.mcp.client import MCPClient, MCPServerSpec
from proseforge_agent.mcp.policy import MCPPolicy


SPEC = MCPServerSpec(id="fs", transport="stdio", command=["x"])


class SpyTransport:
    def __init__(self):
        self.calls = []

    def start(self):
        pass

    def close(self):
        pass

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"ok": True, "content": "ran"}


def _policy(**kw):
    return MCPPolicy(server_id="fs", **kw)


def test_call_tool_denied_by_policy_never_touches_transport():
    transport = SpyTransport()
    policy = _policy(filesystem_allow=["notes/"], write_mode="approval_required")
    client = MCPClient(SPEC, transport=transport, policy=policy)

    result = client.call_tool("write_file", {"path": "../../etc/passwd"})

    assert result.ok is False
    assert "policy" in result.error.lower()
    assert transport.calls == []  # transport must NOT run


def test_call_tool_allowed_by_policy_reaches_transport():
    transport = SpyTransport()
    policy = _policy(filesystem_allow=[], write_mode="read_only")
    client = MCPClient(SPEC, transport=transport, policy=policy)

    result = client.call_tool("read_file", {"path": "notes.md"})

    assert result.ok is True
    assert transport.calls == [("read_file", {"path": "notes.md"})]


def test_approval_required_without_gate_is_denied_clearly():
    transport = SpyTransport()
    policy = _policy(filesystem_allow=[], write_mode="approval_required")
    client = MCPClient(SPEC, transport=transport, policy=policy)

    result = client.call_tool("write_file", {"path": "notes.md"})

    assert result.ok is False
    assert "approval" in result.error.lower()
    assert transport.calls == []


def test_approval_required_with_gate_blocks_until_decided(tmp_path):
    transport = SpyTransport()
    policy = _policy(filesystem_allow=[], write_mode="approval_required")
    gate = MCPApprovalGate(queue=MCPApprovalQueue(tmp_path))
    client = MCPClient(SPEC, transport=transport, policy=policy, approval_gate=gate)

    result = client.call_tool("write_file", {"path": "notes.md"})

    assert result.ok is False
    assert "approval" in result.error.lower()
    assert transport.calls == []  # blocked pending approval


def test_client_without_policy_is_backward_compatible():
    transport = SpyTransport()
    client = MCPClient(SPEC, transport=transport)  # no policy

    result = client.call_tool("write_file", {"path": "../../etc/passwd"})

    assert result.ok is True
    assert transport.calls == [("write_file", {"path": "../../etc/passwd"})]
