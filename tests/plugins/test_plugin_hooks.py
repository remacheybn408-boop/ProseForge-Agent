"""Plugin lifecycle hook tests (Task 149)."""

from __future__ import annotations

from proseforge_agent.plugins import PluginAPI, PluginHookRegistry


def test_plugin_hooks_contract():
    registry = PluginHookRegistry()
    api = PluginAPI(hooks=registry)
    received: list[str] = []

    def register(plugin_api):
        plugin_api.hooks.on_after_export(lambda event: received.append(event["artifact"]))

    register(api)
    result = registry.emit("on_after_export", {"artifact": "book.epub"})

    assert received == ["book.epub"]
    assert result.status == "ok"
    assert result.dispatched == 1


def test_plugin_hooks_isolate_handler_errors():
    registry = PluginHookRegistry()
    received: list[str] = []

    registry.on_after_export(lambda event: (_ for _ in ()).throw(RuntimeError("boom")))
    registry.on_after_export(lambda event: received.append(event["artifact"]))

    result = registry.emit("on_after_export", {"artifact": "book.epub"})

    assert received == ["book.epub"]
    assert result.status == "partial"
    assert result.dispatched == 1
    assert result.errors[0].hook == "on_after_export"
    assert "boom" in result.errors[0].error
