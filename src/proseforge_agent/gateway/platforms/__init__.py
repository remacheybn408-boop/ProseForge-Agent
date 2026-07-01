"""Messaging platform adapter contracts."""

from .base import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult
from .discord import DiscordCheckResult, DiscordGatewayAdapter
from .email import EmailGatewayAdapter
from .mobile_email import GatewayAdapterCheck, OptionalGatewayAdapter
from .slack import SlackCheckResult, SlackGatewayAdapter
from .signal import SignalGatewayAdapter
from .telegram import TelegramCheckResult, TelegramGatewayAdapter
from .whatsapp import WhatsAppGatewayAdapter

__all__ = [
    "AdapterCapabilities",
    "DiscordCheckResult",
    "DiscordGatewayAdapter",
    "EmailGatewayAdapter",
    "FakePlatformAdapter",
    "GatewayAdapterCheck",
    "OutboundMessage",
    "OptionalGatewayAdapter",
    "PlatformAdapter",
    "SendResult",
    "SlackCheckResult",
    "SlackGatewayAdapter",
    "SignalGatewayAdapter",
    "TelegramCheckResult",
    "TelegramGatewayAdapter",
    "WhatsAppGatewayAdapter",
]
