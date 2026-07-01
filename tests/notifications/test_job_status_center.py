"""Job status center tests (Task 142)."""

from __future__ import annotations

from proseforge_agent.notifications import JobStatusCenter
from proseforge_agent.cli import main


def test_job_status_center_records_status_logs_and_cancellation(tmp_path):
    center = JobStatusCenter(tmp_path)

    job = center.create("rag_ingest")
    running = center.update(job.id, "running", log="started")
    completed = center.update(job.id, "completed", log="done")

    assert running.status == "running"
    assert completed.status == "completed"
    assert center.get(job.id).name == "rag_ingest"
    assert [entry.message for entry in center.logs(job.id)] == ["started", "done"]
    assert center.list()[0].id == job.id
    assert center.cancel(job.id).status == "cancelled"


def test_jobs_status_center_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    center = JobStatusCenter(".pf-agent")
    job = center.create("backup")
    center.update(job.id, "running", log="started")

    assert main(["jobs", "list"]) == 0
    assert main(["jobs", "status", job.id]) == 0
    assert main(["jobs", "logs", job.id]) == 0
    assert main(["jobs", "cancel", job.id]) == 0

    out = capsys.readouterr().out
    assert "Job Status Center" in out
    assert job.id in out
    assert "cancelled" in out
