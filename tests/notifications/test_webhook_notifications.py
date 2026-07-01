"""Webhook notification tests (Task 141)."""

from __future__ import annotations

import json

from proseforge_agent.notifications import NotificationEvent, WebhookNotificationChannel
from proseforge_agent.cli import main


def test_webhook_channel_retries_and_does_not_persist_plaintext_url(tmp_path):
    attempts: list[dict] = []

    def transport(url, payload, headers, timeout):
        attempts.append({"url": url, "payload": payload, "headers": headers, "timeout": timeout})
        return {"ok": len(attempts) == 2, "status_code": 200 if len(attempts) == 2 else 500}

    channel = WebhookNotificationChannel(
        enabled=True,
        url_ref="secret://webhook",
        url_resolver=lambda ref: "https://hooks.example/secret-token",
        events=["job_failed"],
        transport=transport,
        retry_count=1,
        timeout_seconds=3,
        signing_secret="signing-secret",
        log_path=tmp_path / "webhook-retries.jsonl",
    )

    result = channel.send(NotificationEvent("job_failed", "Job failed", "rag ingest failed"))

    assert result["status"] == "sent"
    assert result["attempts"] == 2
    assert attempts[0]["headers"]["X-ProseForge-Agent-Signature"]
    retry_log = (tmp_path / "webhook-retries.jsonl").read_text(encoding="utf-8")
    assert "https://hooks.example/secret-token" not in retry_log
    assert "secret://webhook" in retry_log


def test_webhook_channel_skips_unsubscribed_events(tmp_path):
    channel = WebhookNotificationChannel(
        enabled=True,
        url_ref="secret://webhook",
        url_resolver=lambda ref: "https://hooks.example/secret-token",
        events=["approval_required"],
        transport=lambda *args: {"ok": True, "status_code": 200},
        log_path=tmp_path / "webhook-retries.jsonl",
    )

    result = channel.send(NotificationEvent("job_failed", "Job failed", "failed"))

    assert result["status"] == "skipped"
    assert result["reason"] == "event not subscribed"


def test_webhook_notifications_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["notifications", "test", "--webhook"]) == 0

    out = capsys.readouterr().out
    assert "Webhook" in out
    assert "unsupported" in out
    serialized = json.dumps(out)
    assert "https://" not in serialized
