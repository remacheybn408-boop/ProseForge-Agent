"""Notification events and delivery channels."""

from .core import (
    NotificationChannel,
    NotificationDispatchResult,
    NotificationDispatcher,
    NotificationEvent,
)
from .desktop import DesktopNotificationChannel

__all__ = [
    "DesktopNotificationChannel",
    "NotificationChannel",
    "NotificationDispatchResult",
    "NotificationDispatcher",
    "NotificationEvent",
]
