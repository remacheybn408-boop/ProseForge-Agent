from pathlib import Path

import pytest

from proseforge_agent.agent.tools import ToolContext, ToolResult, general_tool_registry
from proseforge_agent.errors import ConfigurationError


class FakeHttpClient:
    def __init__(self) -> None:
        self.urls = []

    def get_text(self, url: str) -> str:
        self.urls.append(url)
        return f"fetched:{url}"

    def search(self, query: str):
        return [{"title": "Result", "url": "https://example.test", "snippet": query}]


def test_fs_read_resolves_inside_workspace(tmp_path):
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    registry = general_tool_registry()
    ctx = ToolContext(workspace_root=tmp_path)

    result = registry.invoke("fs.read", {"path": "notes.txt"}, context=ctx)

    assert isinstance(result, ToolResult)
    assert result.ok is True
    assert result.output == "hello"
    assert result.provenance == "workspace"


def test_fs_write_rejects_path_escape_before_io(tmp_path):
    registry = general_tool_registry()
    ctx = ToolContext(workspace_root=tmp_path)

    with pytest.raises(ConfigurationError):
        registry.invoke("fs.write", {"path": "../outside.txt", "text": "nope"}, context=ctx)

    assert not (tmp_path.parent / "outside.txt").exists()


def test_fs_write_and_edit_stay_inside_workspace(tmp_path):
    registry = general_tool_registry()
    ctx = ToolContext(workspace_root=tmp_path)

    write_result = registry.invoke("fs.write", {"path": "drafts/a.txt", "text": "old line"}, context=ctx)
    edit_result = registry.invoke(
        "fs.edit",
        {"path": "drafts/a.txt", "old": "old", "new": "new"},
        context=ctx,
    )

    assert write_result.ok is True
    assert edit_result.ok is True
    assert (tmp_path / "drafts" / "a.txt").read_text(encoding="utf-8") == "new line"


def test_web_fetch_requires_network_permission(tmp_path):
    registry = general_tool_registry()
    client = FakeHttpClient()
    ctx = ToolContext(workspace_root=tmp_path, network_enabled=False, http_client=client)

    result = registry.invoke("web.fetch", {"url": "https://example.test"}, context=ctx)

    assert result.ok is False
    assert "network permission" in result.error
    assert client.urls == []


def test_web_fetch_marks_external_content_untrusted(tmp_path):
    registry = general_tool_registry()
    client = FakeHttpClient()
    ctx = ToolContext(workspace_root=tmp_path, network_enabled=True, http_client=client)

    result = registry.invoke("web.fetch", {"url": "https://example.test"}, context=ctx)

    assert result.ok is True
    assert result.output == "fetched:https://example.test"
    assert result.provenance == "untrusted"


def test_web_search_uses_injected_client_and_marks_untrusted(tmp_path):
    registry = general_tool_registry()
    client = FakeHttpClient()
    ctx = ToolContext(workspace_root=tmp_path, network_enabled=True, http_client=client)

    result = registry.invoke("web.search", {"query": "demo"}, context=ctx)

    assert result.ok is True
    assert result.output[0]["snippet"] == "demo"
    assert result.provenance == "untrusted"


def test_general_tools_are_registered_with_permissions():
    registry = general_tool_registry()
    assert registry.required_permission("fs.read") == "read_only"
    assert registry.required_permission("fs.write") == "draft_write"
    assert registry.required_permission("fs.edit") == "draft_write"
    assert registry.required_permission("web.fetch") == "read_only"
    assert registry.required_permission("web.search") == "read_only"
