"""Messaging platform adapter contracts."""

from .base import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult
from .telegram import TelegramCheckResult, TelegramGatewayAdapter

__all__ = [
    "AdapterCapabilities",
    "FakePlatformAdapter",
    "OutboundMessage",
    "PlatformAdapter",
    "SendResult",
    "TelegramCheckResult",
    "TelegramGatewayAdapter",
]
