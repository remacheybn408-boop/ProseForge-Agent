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


def test_desktop_notification_commands_quote_shell_payloads():
    event = NotificationEvent("job_failed", "Done'; Remove-Item x; '", 'Job "failed" \\ now')

    windows_script = DesktopNotificationChannel(platform="windows")._command(event)[-1]
    mac_script = DesktopNotificationChannel(platform="darwin")._command(event)[-1]

    assert "-Text 'Done''; Remove-Item x; '''" in windows_script
    assert "'Job \"failed\" \\ now'" in windows_script
    assert 'display notification "Job \\"failed\\" \\\\ now"' in mac_script


def test_desktop_notifications_cli_reports_channel_status(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["notifications", "test", "--desktop"]) == 0

    out = capsys.readouterr().out
    assert "Desktop" in out
    assert "unsupported" in out
