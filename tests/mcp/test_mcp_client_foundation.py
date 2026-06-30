"""MCP client foundation tests (Task 116)."""

from __future__ import annotations

from proseforge_agent.agent.tools import ToolResult
from proseforge_agent.cli import main
from proseforge_agent.mcp import MCPClient, MCPServerSpec, StaticMCPTransport


def test_mcp_client_foundation_contract():
    transport = StaticMCPTransport(
        capabilities={"tools": True, "resources": True, "prompts": True},
        tools=[{"name": "read_file", "description": "Read a file", "input_schema": {"type": "object"}}],
        resources=[{"uri": "file:///demo/notes.md", "name": "notes"}],
        prompts=[{"name": "summarize", "arguments": ["text"]}],
        tool_results={"read_file": {"content": "hello"}},
    )
    client = MCPClient(MCPServerSpec(id="filesystem", transport="stdio", command=["fake-mcp"]), transport=transport)

    client.start()
    capabilities = client.inspect()
    result = client.call_tool("read_file", {"path": "notes.md"})
    client.close()

    assert capabilities.server_id == "filesystem"
    assert capabilities.capabilities["tools"] is True
    assert [tool.name for tool in client.list_tools()] == ["read_file"]
    assert [resource.uri for resource in client.list_resources()] == ["file:///demo/notes.md"]
    assert [prompt.name for prompt in client.list_prompts()] == ["summarize"]
    assert isinstance(result, ToolResult)
    assert result.ok is True
    assert result.output == {"content": "hello"}
    assert result.provenance == "mcp:filesystem"
    assert transport.closed is True


def test_mcp_cli_lists_and_inspects_default_server(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["mcp", "list"]) == 0
    assert main(["mcp", "inspect", "filesystem"]) == 0
    assert main(["mcp", "tools", "filesystem"]) == 0
    assert main(["mcp", "resources", "filesystem"]) == 0

    out = capsys.readouterr().out
    assert "MCP Servers" in out
    assert "filesystem" in out
    assert "read_file" in out
    assert "file:///workspace" in out
