"""Notification events and delivery channels."""

from .core import (
    NotificationChannel,
    NotificationDispatchResult,
    NotificationDispatcher,
    NotificationEvent,
)
from .desktop import DesktopNotificationChannel
from .webhook import WebhookNotificationChannel

__all__ = [
    "DesktopNotificationChannel",
    "NotificationChannel",
    "NotificationDispatchResult",
    "NotificationDispatcher",
    "NotificationEvent",
    "WebhookNotificationChannel",
]
