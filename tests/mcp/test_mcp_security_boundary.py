"""MCP security boundary tests (Task 118)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.mcp import MCPPolicy, MCPPolicyStore


def test_mcp_security_policy_denies_secrets_and_path_escape(tmp_path):
    policy = MCPPolicy(
        server_id="filesystem",
        filesystem_allow=["project"],
        filesystem_deny=["project/private"],
        network_allow=["api.example.com"],
        command_allow=["fake-mcp"],
        project_scope="demo_novel",
        write_mode="approval_required",
    )

    assert policy.decide("secret.read", "OPENAI_API_KEY").allowed is False
    assert policy.decide("fs.read", "project/notes.md").allowed is True
    assert policy.decide("fs.read", "project/private/key.txt").allowed is False
    assert policy.decide("fs.read", "../outside.txt").allowed is False
    assert policy.decide("network.connect", "api.example.com").allowed is True
    assert policy.decide("network.connect", "evil.example.com").allowed is False
    assert policy.decide("command.spawn", "fake-mcp").allowed is True

    write_decision = policy.decide("fs.write", "project/notes.md")
    assert write_decision.allowed is False
    assert write_decision.requires_approval is True


def test_mcp_policy_store_round_trip(tmp_path):
    store = MCPPolicyStore(tmp_path)
    saved = store.set(
        MCPPolicy(
            server_id="filesystem",
            filesystem_allow=["project"],
            network_allow=["api.example.com"],
            command_allow=["fake-mcp"],
        )
    )

    loaded = MCPPolicyStore(tmp_path).get("filesystem")
    assert loaded == saved
    assert store.list()[0].server_id == "filesystem"


def test_mcp_policy_cli_list_show_set(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "mcp",
            "policy",
            "set",
            "filesystem",
            "--filesystem-allow",
            "project",
            "--network-allow",
            "api.example.com",
            "--command-allow",
            "fake-mcp",
            "--write-mode",
            "approval_required",
        ]
    ) == 0
    assert main(["mcp", "policy", "list"]) == 0
    assert main(["mcp", "policy", "show", "filesystem"]) == 0

    out = capsys.readouterr().out
    assert "MCP Policy" in out
    assert "filesystem" in out
    assert "approval_required" in out
