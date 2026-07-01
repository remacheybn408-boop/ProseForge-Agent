"""Notification events and delivery channels."""

from .core import (
    NotificationChannel,
    NotificationDispatchResult,
    NotificationDispatcher,
    NotificationEvent,
)
from .desktop import DesktopNotificationChannel
from .jobs import JOB_STATUSES, JobLogEntry, JobRecord, JobStatusCenter
from .webhook import WebhookNotificationChannel

__all__ = [
    "DesktopNotificationChannel",
    "JOB_STATUSES",
    "JobLogEntry",
    "JobRecord",
    "JobStatusCenter",
    "NotificationChannel",
    "NotificationDispatchResult",
    "NotificationDispatcher",
    "NotificationEvent",
    "WebhookNotificationChannel",
]
