"""Platform adapter contract tests (Task 156)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.gateway import OutboundMessage
from proseforge_agent.gateway.platforms.base import FakePlatformAdapter


def test_fake_adapter_round_trips_message_event():
    adapter = FakePlatformAdapter(
        inbound=[
            {
                "chat_id": "chat-1",
                "user_id": "user-1",
                "thread_id": "thread-1",
                "message_id": "msg-1",
                "text": "hello",
                "raw": {"token": "secret-token"},
            }
        ]
    )

    event = next(adapter.poll_or_listen())
    result = adapter.send(OutboundMessage(platform="fake", chat_id=event.chat_id, thread_id=event.thread_id, text="reply"))

    assert event.platform == "fake"
    assert event.text == "hello"
    assert result.delivered is True
    assert result.message_ids == ["fake-1"]
    assert result.raw_metadata["token"] == "[redacted]"


def test_adapter_reports_capabilities_and_size_limits():
    adapter = FakePlatformAdapter(max_message_size=5)

    assert adapter.capabilities.threads is True
    result = adapter.send(OutboundMessage(platform="fake", chat_id="chat", thread_id="", text="too long"))
    assert result.delivered is False
    assert result.retryable is False
    assert "max message size" in result.reason


def test_gateway_platforms_cli_lists_fake_adapter(capsys):
    assert main(["gateway", "platforms", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Gateway Platforms" in out
    assert "fake" in out
