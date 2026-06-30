"""MCP server registry tests (Task 117)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.mcp import MCPServerConfig, MCPServerRegistry


def test_mcp_server_registry_persists_full_server_config(tmp_path):
    registry = MCPServerRegistry(tmp_path)

    config = registry.add(
        MCPServerConfig(
            id="filesystem",
            display_name="Filesystem",
            transport="stdio",
            command=["npx", "@modelcontextprotocol/server-filesystem"],
            env={"MODE": "test"},
            cwd=".",
            enabled=True,
            trust_level="local",
            permission_profile="read_only",
            timeout_ms=5000,
            rate_limit_per_minute=30,
        )
    )

    loaded = MCPServerRegistry(tmp_path).get("filesystem")
    assert loaded == config
    assert loaded.to_spec().transport == "stdio"
    assert registry.disable("filesystem").enabled is False
    assert registry.enable("filesystem").enabled is True
    updated = registry.configure("filesystem", timeout_ms=1000, rate_limit_per_minute=10)
    assert updated.timeout_ms == 1000
    assert updated.rate_limit_per_minute == 10
    assert registry.remove("filesystem").id == "filesystem"
    assert registry.list() == []


def test_mcp_registry_cli_add_config_enable_disable_remove(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["mcp", "add", "filesystem", "--transport", "stdio", "--command", "fake-mcp"]) == 0
    assert main(["mcp", "config", "filesystem", "--timeout", "2000", "--rate-limit", "5"]) == 0
    assert main(["mcp", "disable", "filesystem"]) == 0
    assert main(["mcp", "enable", "filesystem"]) == 0
    assert main(["mcp", "list"]) == 0
    assert main(["mcp", "remove", "filesystem"]) == 0

    out = capsys.readouterr().out
    assert "MCP Server Config" in out
    assert "filesystem" in out
    assert "enabled=True" in out
