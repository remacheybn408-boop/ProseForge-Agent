"""MCP credentials boundary tests (Task 121)."""

from __future__ import annotations

from proseforge_agent.mcp import MCPApprovalQueue, MCPCredentialBoundary, MCPServerConfig


def test_mcp_credentials_boundary_does_not_inherit_full_environment():
    config = MCPServerConfig(
        id="filesystem",
        transport="stdio",
        command=["fake-mcp"],
        env={"STATIC": "1"},
        env_allow=["SAFE_VAR"],
        secret_refs={"API_KEY": "secret://mcp/filesystem/api_key"},
    )
    boundary = MCPCredentialBoundary(secret_resolver=lambda ref: "sk-secret" if ref else "")

    env = boundary.build_env(
        config,
        source_env={"SAFE_VAR": "ok", "OPENAI_API_KEY": "sk-real", "PATH": "ignored"},
    )

    assert env == {"STATIC": "1", "SAFE_VAR": "ok", "API_KEY": "sk-secret"}
    assert "OPENAI_API_KEY" not in env
    assert "PATH" not in env


def test_mcp_credentials_redaction_covers_logs_and_approval_payloads(tmp_path):
    queue = MCPApprovalQueue(tmp_path)
    request = queue.submit(
        server_id="filesystem",
        tool_name="write_file",
        arguments={"path": "drafts/ch_001.md", "api_key": "sk-secret", "nested": {"token": "tok-secret"}},
    )

    raw = (tmp_path / "approvals" / "mcp_queue.json").read_text(encoding="utf-8")
    assert "sk-secret" not in raw
    assert "tok-secret" not in raw
    assert request.payload["arguments"]["api_key"] == "[redacted]"
    assert request.payload["arguments"]["nested"]["token"] == "[redacted]"
