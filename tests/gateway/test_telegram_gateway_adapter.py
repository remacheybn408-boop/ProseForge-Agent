"""Telegram gateway adapter tests (Task 157)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import OutboundMessage
from proseforge_agent.gateway.platforms.telegram import TelegramGatewayAdapter


def test_telegram_update_maps_to_message_event():
    update = {
        "message": {
            "message_id": 42,
            "text": "hello telegram",
            "chat": {"id": 12345},
            "from": {"id": 67890},
            "message_thread_id": 7,
        }
    }

    event = TelegramGatewayAdapter(token="secret-token").parse_update(update)

    assert event.platform == "telegram"
    assert event.chat_id == "12345"
    assert event.user_id == "67890"
    assert event.thread_id == "7"
    assert event.message_id == "42"
    assert event.text == "hello telegram"


def test_telegram_send_chunks_and_redacts_token():
    adapter = TelegramGatewayAdapter(token="secret-token", max_message_size=5, allow_fake_transport=True)

    result = adapter.send(OutboundMessage(platform="telegram", chat_id="12345", thread_id="7", text="hello world"))

    assert result.delivered is True
    assert result.message_ids == ["telegram-1", "telegram-2", "telegram-3"]
    assert result.raw_metadata["token"] == "[redacted]"
    assert result.raw_metadata["chat_id"] == "[redacted]"


def test_telegram_stop_command_maps_to_control_metadata():
    event = TelegramGatewayAdapter(token="secret-token").parse_update(
        {
            "message": {
                "message_id": 1,
                "text": "/stop",
                "chat": {"id": 1},
                "from": {"id": 2},
            }
        }
    )

    assert event.authorization["command"] == "stop"


def test_telegram_cli_check_dry_run(capsys):
    assert main(["gateway", "telegram", "check", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Telegram Gateway" in out
    assert "dry_run=true" in out
