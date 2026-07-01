"""Hosted cron and scale-to-zero lifecycle tests (Task 180)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.cron import CronJob, HostedCronVerifier, IdempotencyStore, ScaleToZeroPlanner


def test_cron_fire_requires_valid_audience_and_nonce(tmp_path):
    verifier = HostedCronVerifier(
        audience="proseforge-agent",
        idempotency=IdempotencyStore(tmp_path),
    )
    payload = verifier.fixture_payload(job_id="daily-report", nonce="nonce-1")

    accepted = verifier.verify(payload)
    wrong_audience = verifier.verify(payload | {"audience": "other", "nonce": "nonce-2"})

    assert accepted.status == "accepted"
    assert wrong_audience.status == "blocked"
    assert "audience" in wrong_audience.reason


def test_cron_fire_rejects_duplicate_nonce(tmp_path):
    verifier = HostedCronVerifier("proseforge-agent", IdempotencyStore(tmp_path))
    payload = verifier.fixture_payload(job_id="daily-report", nonce="nonce-1")

    first = verifier.verify(payload)
    duplicate = verifier.verify(payload)

    assert first.status == "accepted"
    assert duplicate.status == "duplicate"


def test_cron_fire_rejects_expired_payload(tmp_path):
    verifier = HostedCronVerifier("proseforge-agent", IdempotencyStore(tmp_path))
    payload = verifier.fixture_payload(job_id="daily-report", nonce="nonce-1", expires_in_seconds=-1)

    result = verifier.verify(payload)

    assert result.status == "blocked"
    assert "expired" in result.reason


def test_scale_to_zero_wake_plan_includes_lifecycle_states():
    plan = ScaleToZeroPlanner().plan(CronJob(name="daily report", schedule="0 9 * * *", job_id="daily-report"))

    assert plan.states == ["wake", "run", "deliver", "hibernate"]
    assert plan.local_fallback is True


def test_cron_cli_add_dry_run(capsys):
    assert main(["cron", "add", "daily report", "--schedule", "0 9 * * *", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Hosted Cron" in out
    assert "daily report" in out


def test_cron_cli_fire_fixture(capsys):
    assert main(["cron", "fire", "--fixture", "demo", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Cron Fire" in out
    assert "accepted" in out
