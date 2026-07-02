import json
from pathlib import Path

from proseforge_agent.agent.events import BackgroundJobRunner, EventBus, redact_sensitive
from proseforge_agent.cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "agent-event-bus-and-background-jobs" / "events_seed.jsonl"


def test_event_bus_appends_jsonl_and_redacts_sensitive_payload(tmp_path):
    path = tmp_path / "events.jsonl"
    record = EventBus(path).emit(
        "provider.request",
        {
            "api_key": "sk-secret",
            "nested": {"token": "tok-secret"},
            "message": "ok",
        },
    )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["payload"]["api_key"] == "[redacted]"
    assert rows[0]["payload"]["nested"]["token"] == "[redacted]"
    assert "sk-secret" not in path.read_text(encoding="utf-8")
    assert record.event_type == "provider.request"


def test_event_bus_is_append_only(tmp_path):
    path = tmp_path / "events.jsonl"
    bus = EventBus(path)
    bus.emit("first", {"count": 1})
    bus.emit("second", {"count": 2})
    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    assert json.loads(rows[0])["event_type"] == "first"
    assert json.loads(rows[1])["event_type"] == "second"


def test_background_job_runner_allows_memory_index_dry_run(tmp_path):
    bus = EventBus(tmp_path / "events.jsonl")
    result = BackgroundJobRunner(event_bus=bus).run(
        "memory-index",
        provider="fake",
        dry_run=True,
    )
    assert result.status == "dry_run"
    assert result.job_name == "memory-index"
    assert result.allowed is True
    assert "memory-index" in (tmp_path / "events.jsonl").read_text(encoding="utf-8")


def test_background_job_runner_rejects_unknown_job(tmp_path):
    result = BackgroundJobRunner(event_bus=EventBus(tmp_path / "events.jsonl")).run(
        "shell",
        provider="fake",
        dry_run=True,
    )
    assert result.status == "denied"
    assert result.allowed is False


def test_events_fixture_is_redacted_jsonl():
    rows = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["payload"]["api_key"] == "[redacted]"


def test_redact_sensitive_covers_common_token_variants():
    payload = {
        "access_token": "a" * 40,
        "refresh_token": "b" * 40,
        "message": "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature x-api-key: sk-secret",
    }
    serialized = json.dumps(redact_sensitive(payload), ensure_ascii=False)

    assert "a" * 40 not in serialized
    assert "b" * 40 not in serialized
    assert "eyJhbGci" not in serialized
    assert "sk-secret" not in serialized


def test_jobs_run_cli_dry_run(capsys):
    code = main(["jobs", "run", "memory-index", "--provider", "fake", "--dry-run"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Background Job" in out
    assert "memory-index" in out
    assert "dry_run" in out
