"""Platform-neutral messaging gateway."""

from .core import DeliveryJob, GatewayResult, GatewayRunner, MessageEvent

__all__ = ["DeliveryJob", "GatewayResult", "GatewayRunner", "MessageEvent"]
