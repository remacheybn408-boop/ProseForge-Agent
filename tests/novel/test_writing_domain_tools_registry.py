"""Writing domain tool registry tests (Task 95)."""

from __future__ import annotations

from proseforge_agent.agent.tools import default_tool_registry
from proseforge_agent.cli import main


def test_writing_domain_tools_registry_contract():
    registry = default_tool_registry()
    tools = registry.list(domain="writing")
    aliases = {alias for tool in tools for alias in tool.aliases}

    assert aliases == {
        "/expand-scene",
        "/condense-chapter",
        "/polish-dialogue",
        "/enhance-description",
        "/check-chronology",
        "/suggest-title",
        "/outline-chapter",
    }
    assert all(tool.domain == "writing" for tool in tools)
    assert all(tool.input_schema for tool in tools)
    assert all(tool.output_schema for tool in tools)
    assert all(tool.permission in {"read_only", "draft_write"} for tool in tools)


def test_writing_domain_tool_executes_structured_result():
    registry = default_tool_registry()

    result = registry.execute("writing.expand_scene", {"text": "A quiet arrival."})

    assert result["ok"] is True
    assert result["tool"] == "writing.expand_scene"
    assert result["result"]["operation"] == "expand_scene"
    assert result["result"]["structured"] is True


def test_tools_cli_filters_writing_domain(capsys):
    assert main(["tools", "list", "--domain", "writing", "--include-permissions"]) == 0

    out = capsys.readouterr().out
    assert "/expand-scene" in out
    assert "/outline-chapter" in out
    assert "install.doctor" not in out
