"""Plugin sandbox tests (Task 147)."""

from __future__ import annotations

from proseforge_agent.plugins import PluginSandbox, PluginSandboxPolicy


def test_plugin_sandbox_scopes_file_access_to_project(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "note.txt").write_text("hello", encoding="utf-8")
    sandbox = PluginSandbox(PluginSandboxPolicy(project_root=project_root))

    assert sandbox.api.read_file("note.txt") == "hello"
    assert sandbox.api.read_file("../secret.txt") is None


def test_plugin_sandbox_isolates_plugin_errors_and_hides_secrets(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    sandbox = PluginSandbox(PluginSandboxPolicy(project_root=project_root, secrets={"TOKEN": "secret"}))

    result = sandbox.run(lambda api: (_ for _ in ()).throw(RuntimeError("boom")))

    assert result.status == "failed"
    assert "boom" in result.error
    assert sandbox.api.get_secret("TOKEN") is None
