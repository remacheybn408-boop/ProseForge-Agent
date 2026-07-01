"""Managed tool gateway foundation tests (Task 169)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.tools.managed import (
    ManagedToolDeclaration,
    ManagedToolGateway,
    ManagedToolInvocationContext,
)


def test_gateway_invocation_enforces_tool_declaration():
    gateway = ManagedToolGateway.fake(
        declarations=[
            ManagedToolDeclaration(
                name="web.search",
                permission="read_only",
                credential_scope="web",
                output_limit=80,
            ),
            ManagedToolDeclaration(
                name="project.publish",
                permission="project_write",
                credential_scope="publishing",
            ),
        ],
        credentials={"web": "secret-web-token", "publishing": "secret-publish-token"},
    )

    allowed = gateway.invoke(
        "web.search",
        {"query": "ProseForge demo"},
        ManagedToolInvocationContext(permission_ceiling="read_only", credential_scopes={"web"}),
    )
    denied = gateway.invoke(
        "project.publish",
        {"target": "draft"},
        ManagedToolInvocationContext(permission_ceiling="read_only", credential_scopes={"publishing"}),
    )
    unknown = gateway.invoke(
        "web.fetch",
        {"url": "https://example.com"},
        ManagedToolInvocationContext(permission_ceiling="system_write", credential_scopes={"web"}),
    )

    assert allowed.status == "ok"
    assert allowed.output["tool"] == "web.search"
    assert allowed.output["payload"]["query"] == "ProseForge demo"
    assert allowed.credentials == {"web": "[redacted]"}
    assert denied.status == "denied"
    assert denied.required_permission == "project_write"
    assert unknown.status == "unknown_tool"


def test_gateway_requires_declared_credential_scope():
    gateway = ManagedToolGateway.fake(
        declarations=[
            ManagedToolDeclaration(
                name="web.search",
                permission="read_only",
                credential_scope="web",
            )
        ],
        credentials={"web": "secret-web-token"},
    )

    result = gateway.invoke(
        "web.search",
        {"query": "missing credential scope"},
        ManagedToolInvocationContext(permission_ceiling="read_only", credential_scopes=set()),
    )

    assert result.status == "denied"
    assert "credential scope" in result.reason
    assert "secret-web-token" not in result.reason


def test_tools_gateway_cli_check(capsys):
    assert main(["tools", "gateway", "check", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Managed Tool Gateway" in out
    assert "web.search" in out
