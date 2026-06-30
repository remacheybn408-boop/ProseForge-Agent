"""MCP tool approval gate tests (Task 119)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.mcp import MCPApprovalGate, MCPApprovalQueue, MCPPolicy


def test_mcp_tool_approval_gate_contract(tmp_path):
    queue = MCPApprovalQueue(tmp_path)
    gate = MCPApprovalGate(queue=queue, known_tools={"read_file"})

    safe = gate.enqueue_if_required(
        server_id="filesystem",
        tool_name="read_file",
        arguments={"path": "drafts/ch_001.md"},
        policy=MCPPolicy(server_id="filesystem", filesystem_allow=["drafts"]),
    )
    risky = gate.enqueue_if_required(
        server_id="filesystem",
        tool_name="write_file",
        arguments={"path": "drafts/ch_001.md", "text": "new draft"},
        policy=MCPPolicy(server_id="filesystem", filesystem_allow=["drafts"], write_mode="approval_required"),
    )

    assert safe is None
    assert risky is not None
    assert risky.status == "pending"
    assert risky.action == "mcp_tool_call"
    assert "write_file" in risky.summary
    assert queue.list()[0].id == risky.id

    approved = queue.approve(risky.id)
    assert approved.status == "approved"


def test_mcp_tool_unknown_network_secret_delete_are_risky(tmp_path):
    gate = MCPApprovalGate(queue=MCPApprovalQueue(tmp_path), known_tools={"read_file"})

    for tool_name in ("unknown_tool", "delete_file", "network_fetch", "read_secret", "shell_exec"):
        request = gate.enqueue_if_required(
            server_id="filesystem",
            tool_name=tool_name,
            arguments={"target": "x"},
            policy=MCPPolicy(server_id="filesystem"),
        )
        assert request is not None


def test_global_approval_cli_lists_approves_and_rejects_mcp_requests(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    queue = MCPApprovalQueue(".pf-agent")
    first = queue.submit(server_id="filesystem", tool_name="write_file", arguments={"path": "drafts/ch_001.md"})
    second = queue.submit(server_id="filesystem", tool_name="delete_file", arguments={"path": "drafts/ch_002.md"})

    assert main(["approval", "list"]) == 0
    assert main(["approval", "approve", first.id]) == 0
    assert main(["approval", "reject", second.id]) == 0

    out = capsys.readouterr().out
    assert "Approval Queue" in out
    assert "mcp_tool_call" in out
    assert "approved" in out
    assert "rejected" in out
