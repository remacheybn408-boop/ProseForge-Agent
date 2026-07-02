"""Persistent job status center."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..concurrency import FileLock
from ..errors import ConfigurationError

JOB_STATUSES = {"queued", "running", "completed", "failed", "cancelled", "retrying"}


@dataclass(frozen=True)
class JobRecord:
    """One background job status record."""

    id: str
    name: str
    status: str = "queued"
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class JobLogEntry:
    """One job log entry."""

    job_id: str
    message: str
    status: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class JobStatusCenter:
    """Filesystem-backed job status and log center."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.jobs_path = self.root / "jobs" / "jobs.jsonl"
        self.logs_path = self.root / "jobs" / "logs.jsonl"
        self.lock_path = self.root / "jobs" / ".jobs.lock"

    def create(self, name: str, *, metadata: dict | None = None) -> JobRecord:
        now = _now()
        job = JobRecord(
            id=f"job_{uuid4().hex[:12]}",
            name=name,
            status="queued",
            created_at=now,
            updated_at=now,
            metadata=dict(metadata or {}),
        )
        with self._lock():
            jobs = self._list_unlocked()
            jobs.append(job)
            self._write_jobs_unlocked(jobs)
        return job

    def update(self, job_id: str, status: str, *, log: str | None = None) -> JobRecord:
        if status not in JOB_STATUSES:
            raise ConfigurationError(f"unsupported job status: {status}")
        with self._lock():
            jobs = self._list_unlocked()
            updated: JobRecord | None = None
            next_jobs: list[JobRecord] = []
            for job in jobs:
                if job.id == job_id:
                    updated = JobRecord(
                        id=job.id,
                        name=job.name,
                        status=status,
                        created_at=job.created_at,
                        updated_at=_now(),
                        metadata=dict(job.metadata),
                    )
                    next_jobs.append(updated)
                else:
                    next_jobs.append(job)
            if updated is None:
                raise ConfigurationError(f"job not found: {job_id}")
            self._write_jobs_unlocked(next_jobs)
            if log:
                self._append_log_unlocked(
                    JobLogEntry(job_id=job_id, message=log, status=status, created_at=updated.updated_at)
                )
            return updated

    def cancel(self, job_id: str) -> JobRecord:
        return self.update(job_id, "cancelled", log="cancel requested")

    def get(self, job_id: str) -> JobRecord:
        for job in self.list():
            if job.id == job_id:
                return job
        raise ConfigurationError(f"job not found: {job_id}")

    def list(self) -> list[JobRecord]:
        with self._lock():
            return self._list_unlocked()

    def logs(self, job_id: str) -> list[JobLogEntry]:
        with self._lock():
            entries = self._logs_unlocked()
        return [entry for entry in entries if entry.job_id == job_id]

    def _lock(self) -> FileLock:
        return FileLock(self.lock_path)

    def _list_unlocked(self) -> list[JobRecord]:
        if not self.jobs_path.exists():
            return []
        return [_job_from_dict(json.loads(line)) for line in self.jobs_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    def _logs_unlocked(self) -> list[JobLogEntry]:
        if not self.logs_path.exists():
            return []
        return [_log_from_dict(json.loads(line)) for line in self.logs_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    def _write_jobs_unlocked(self, jobs: list[JobRecord]) -> None:
        self.jobs_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.jobs_path.with_suffix(self.jobs_path.suffix + ".tmp")
        tmp_path.write_text(
            "".join(json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for job in jobs),
            encoding="utf-8",
        )
        tmp_path.replace(self.jobs_path)

    def _append_log_unlocked(self, entry: JobLogEntry) -> None:
        self.logs_path.parent.mkdir(parents=True, exist_ok=True)
        with self.logs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _job_from_dict(payload: dict) -> JobRecord:
    return JobRecord(
        id=str(payload["id"]),
        name=str(payload["name"]),
        status=str(payload.get("status", "queued")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        metadata=dict(payload.get("metadata") or {}),
    )


def _log_from_dict(payload: dict) -> JobLogEntry:
    return JobLogEntry(
        job_id=str(payload["job_id"]),
        message=str(payload.get("message", "")),
        status=str(payload.get("status", "")),
        created_at=str(payload.get("created_at", "")),
    )


__all__ = ["JOB_STATUSES", "JobLogEntry", "JobRecord", "JobStatusCenter"]
