"""Desktop notification tests (Task 140)."""

from __future__ import annotations

from proseforge_agent.notifications import DesktopNotificationChannel, NotificationEvent
from proseforge_agent.cli import main


def test_desktop_notification_channel_uses_injected_runner():
    commands: list[list[str]] = []

    def runner(command):
        commands.append(command)
        return {"returncode": 0}

    channel = DesktopNotificationChannel(platform="linux", enabled=True, runner=runner)
    result = channel.send(NotificationEvent("job_completed", "Done", "Job completed"))

    assert result["status"] == "sent"
    assert commands[0][:2] == ["notify-send", "Done"]


def test_desktop_notification_channel_reports_unsupported_without_runner():
    channel = DesktopNotificationChannel(platform="windows", enabled=True)

    result = channel.send(NotificationEvent("job_completed", "Done", "Job completed"))

    assert result["status"] == "unsupported"
    assert "runner" in result["reason"]


def test_desktop_notifications_cli_reports_channel_status(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["notifications", "test", "--desktop"]) == 0

    out = capsys.readouterr().out
    assert "Desktop" in out
    assert "unsupported" in out
