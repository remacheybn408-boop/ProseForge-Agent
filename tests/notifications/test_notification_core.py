"""Notification core tests (Task 139)."""

from __future__ import annotations

import json

from proseforge_agent.notifications import NotificationDispatcher, NotificationEvent
from proseforge_agent.cli import main


class RecordingChannel:
    name = "recording"

    def __init__(self) -> None:
        self.events: list[NotificationEvent] = []

    def send(self, event: NotificationEvent):
        self.events.append(event)
        return {"channel": self.name, "status": "sent"}


def test_notification_dispatcher_writes_events_and_notifies_channels(tmp_path):
    channel = RecordingChannel()
    dispatcher = NotificationDispatcher(tmp_path, channels=[channel])
    event = NotificationEvent(event_type="job_completed", title="Job done", message="memory-index completed")

    result = dispatcher.dispatch(event)

    assert result.event_id == event.id
    assert result.channel_results == [{"channel": "recording", "status": "sent"}]
    assert channel.events == [event]
    rows = [json.loads(line) for line in (tmp_path / "notifications" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["event_type"] == "job_completed"
    assert dispatcher.list_events()[0].title == "Job done"


def test_notifications_cli_list_and_test(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["notifications", "test"]) == 0
    assert main(["notifications", "list"]) == 0

    out = capsys.readouterr().out
    assert "Notifications" in out
    assert "notification_test" in out
