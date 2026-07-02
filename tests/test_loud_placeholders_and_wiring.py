"""Loud placeholders + doctor wiring section (Task 202, findings 4.1/5.2)."""

from __future__ import annotations

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.doctor import InstallationDoctor
from proseforge_agent.mcp.client import (
    MCPServerSpec,
    PlaceholderMCPTransport,
    StdioMCPTransport,
)


def _stdio_spec():
    return MCPServerSpec(id="fs", transport="stdio", command=["fake-mcp"])


def _http_spec():
    return MCPServerSpec(id="web", transport="http", url="https://example/mcp")


def test_doctor_wiring_section_reports_transport_bindings():
    report = InstallationDoctor().run(section="wiring")
    names = {check.name for check in report.checks}
    assert "mcp" in names
    assert any(name.startswith("gateway.") for name in names)
    assert any(name.startswith("environment.") for name in names)
    assert all(check.section == "wiring" for check in report.checks)


def test_placeholder_stdio_start_raises_without_env_flag(monkeypatch):
    monkeypatch.delenv("PF_AGENT_ALLOW_PLACEHOLDER_MCP", raising=False)
    with pytest.raises(ConfigurationError) as exc:
        StdioMCPTransport(_stdio_spec()).start()
    assert "placeholder" in str(exc.value).lower()


def test_placeholder_stdio_start_allowed_with_env_flag(monkeypatch):
    monkeypatch.setenv("PF_AGENT_ALLOW_PLACEHOLDER_MCP", "1")
    transport = StdioMCPTransport(_stdio_spec())
    transport.start()
    assert transport.started is True


def test_placeholder_http_start_raises_without_env_flag(monkeypatch):
    monkeypatch.delenv("PF_AGENT_ALLOW_PLACEHOLDER_MCP", raising=False)
    with pytest.raises(ConfigurationError):
        PlaceholderMCPTransport(_http_spec()).start()


def test_cli_doctor_section_wiring_smoke(capsys):
    code = main(["doctor", "--section", "wiring"])
    assert code == 0
    out = capsys.readouterr().out
    assert "mcp" in out.lower()
