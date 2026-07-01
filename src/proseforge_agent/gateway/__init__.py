"""Platform-neutral messaging gateway."""

from .core import DeliveryJob, GatewayResult, GatewayRunner, MessageEvent
from .platforms import AdapterCapabilities, FakePlatformAdapter, OutboundMessage, PlatformAdapter, SendResult
from .relay import PairingToken, RelayAuthDecision, RelayAuthenticator, RelayPairingService

__all__ = [
    "AdapterCapabilities",
    "DeliveryJob",
    "FakePlatformAdapter",
    "GatewayResult",
    "GatewayRunner",
    "MessageEvent",
    "OutboundMessage",
    "PairingToken",
    "PlatformAdapter",
    "RelayAuthDecision",
    "RelayAuthenticator",
    "RelayPairingService",
    "SendResult",
]
