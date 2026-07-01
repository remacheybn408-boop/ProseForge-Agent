"""Messaging platform adapter contracts."""

from .base import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult
from .discord import DiscordCheckResult, DiscordGatewayAdapter
from .slack import SlackCheckResult, SlackGatewayAdapter
from .telegram import TelegramCheckResult, TelegramGatewayAdapter

__all__ = [
    "AdapterCapabilities",
    "DiscordCheckResult",
    "DiscordGatewayAdapter",
    "FakePlatformAdapter",
    "OutboundMessage",
    "PlatformAdapter",
    "SendResult",
    "SlackCheckResult",
    "SlackGatewayAdapter",
    "TelegramCheckResult",
    "TelegramGatewayAdapter",
]
