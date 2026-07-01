"""Discord and Slack gateway adapter tests (Task 158)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import OutboundMessage
from proseforge_agent.gateway.platforms.discord import DiscordGatewayAdapter
from proseforge_agent.gateway.platforms.slack import SlackGatewayAdapter


def test_discord_and_slack_events_share_contract():
    discord_event = DiscordGatewayAdapter(token="discord-secret").parse_event(
        {
            "id": "msg-1",
            "channel_id": "chan-1",
            "author": {"id": "user-1"},
            "thread_id": "thread-1",
            "content": "hello discord",
        }
    )
    slack_event = SlackGatewayAdapter(token="slack-secret").parse_event(
        {
            "ts": "1700000000.0001",
            "channel": "chan-2",
            "user": "user-2",
            "thread_ts": "thread-2",
            "text": "hello slack",
        }
    )

    assert discord_event.platform == "discord"
    assert slack_event.platform == "slack"
    assert discord_event.thread_id == "thread-1"
    assert slack_event.thread_id == "thread-2"


def test_discord_and_slack_send_redacts_auth_and_reports_capabilities():
    discord = DiscordGatewayAdapter(token="discord-secret")
    slack = SlackGatewayAdapter(token="slack-secret")

    discord_result = discord.send(OutboundMessage(platform="discord", chat_id="chan-1", thread_id="thread-1", text="reply"))
    slack_result = slack.send(OutboundMessage(platform="slack", chat_id="chan-2", thread_id="thread-2", text="reply"))

    assert discord.capabilities.threads is True
    assert slack.capabilities.threads is True
    assert discord_result.raw_metadata["token"] == "[redacted]"
    assert slack_result.raw_metadata["token"] == "[redacted]"


def test_discord_slack_cli_checks(capsys):
    assert main(["gateway", "discord", "check", "--dry-run"]) == 0
    assert main(["gateway", "slack", "check", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Discord Gateway" in out
    assert "Slack Gateway" in out
