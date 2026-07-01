"""Messaging platform adapter contracts."""

from .base import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult

__all__ = [
    "AdapterCapabilities",
    "FakePlatformAdapter",
    "OutboundMessage",
    "PlatformAdapter",
    "SendResult",
]
