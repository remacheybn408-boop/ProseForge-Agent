"""Named gateway adapters refuse fake delivery by default (Task/finding 4.2)."""

from __future__ import annotations

import pytest

from proseforge_agent.gateway.platforms.base import OutboundMessage
from proseforge_agent.gateway.platforms.discord import DiscordGatewayAdapter
from proseforge_agent.gateway.platforms.mobile_email import OptionalGatewayAdapter
from proseforge_agent.gateway.platforms.slack import SlackGatewayAdapter
from proseforge_agent.gateway.platforms.telegram import TelegramGatewayAdapter


def _msg(platform):
    return OutboundMessage(platform=platform, chat_id="c", thread_id="", text="hi")


ADAPTERS = [
    (TelegramGatewayAdapter, "telegram"),
    (DiscordGatewayAdapter, "discord"),
    (SlackGatewayAdapter, "slack"),
    (OptionalGatewayAdapter, "optional"),
]


@pytest.mark.parametrize("cls,platform", ADAPTERS)
def test_send_refuses_without_allow_fake_transport(cls, platform):
    adapter = cls()
    result = adapter.send(_msg(getattr(adapter, "platform", platform)))
    assert result.delivered is False
    assert "fake transport" in result.reason.lower()


@pytest.mark.parametrize("cls,platform", ADAPTERS)
def test_send_delivers_with_allow_fake_transport(cls, platform):
    adapter = cls(allow_fake_transport=True)
    result = adapter.send(_msg(getattr(adapter, "platform", platform)))
    assert result.delivered is True


def test_edit_refuses_without_allow_fake_transport():
    adapter = TelegramGatewayAdapter()
    result = adapter.edit(OutboundMessage(platform="telegram", chat_id="c", thread_id="", text="x", message_id="m1"))
    assert result.delivered is False
    assert "fake transport" in result.reason.lower()
