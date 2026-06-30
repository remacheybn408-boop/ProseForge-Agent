"""Offline mode tests (Task 125)."""

from __future__ import annotations

from proseforge_agent.agent.offline import OfflinePolicy
from proseforge_agent.cli import main


def test_offline_policy_allows_local_features_and_blocks_remote_actions():
    policy = OfflinePolicy()

    assert policy.check("chat", provider="fake").allowed is True
    assert policy.check("doctor").allowed is True
    assert policy.check("export", export_format="txt").allowed is True
    assert policy.check("mcp", tool_name="fs.read").allowed is True

    remote_chat = policy.check("chat", provider="openai")
    mcp_network = policy.check("mcp", tool_name="network.fetch")
    cloud_sync = policy.check("cloud_sync")

    assert remote_chat.allowed is False
    assert remote_chat.reason == "remote provider calls are blocked in offline mode"
    assert mcp_network.allowed is False
    assert cloud_sync.allowed is False


def test_offline_cli_status_and_fake_chat(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["offline", "status"]) == 0
    assert main(["--offline", "chat", "--message", "hello", "--provider", "fake"]) == 0
    assert main(["--offline", "chat", "--message", "hello", "--provider", "openai"]) == 2

    out = capsys.readouterr().out
    assert "Offline Mode" in out
    assert "fake provider chat" in out
    assert "remote provider calls are blocked" in out
