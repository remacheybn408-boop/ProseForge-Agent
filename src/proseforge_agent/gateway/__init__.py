"""Platform-neutral messaging gateway."""

from .core import DeliveryJob, GatewayResult, GatewayRunner, MessageEvent
from .platforms import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult

__all__ = [
    "AdapterCapabilities",
    "DeliveryJob",
    "FakePlatformAdapter",
    "GatewayResult",
    "GatewayRunner",
    "MessageEvent",
    "OutboundMessage",
    "PlatformAdapter",
    "SendResult",
]
