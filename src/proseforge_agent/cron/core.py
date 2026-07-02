"""Hosted cron verification and lifecycle contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import threading
from pathlib import Path
import time
from typing import Any

from ..concurrency import FileLock


@dataclass(frozen=True)
class CronJob:
    """Dry-run cron job contract."""

    name: str
    schedule: str
    job_id: str = ""
    delivery_target: str = "local-agent"

    def __post_init__(self) -> None:
        if not self.job_id:
            object.__setattr__(self, "job_id", _slug(self.name))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "job_id": self.job_id,
            "delivery_target": self.delivery_target,
        }


@dataclass(frozen=True)
class CronFireResult:
    """Verification result for an inbound hosted cron fire."""

    status: str
    reason: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "reason": self.reason, "payload": self.payload}


@dataclass(frozen=True)
class ScaleToZeroPlan:
    """Lifecycle plan for waking a sleeping non-desktop agent."""

    job_id: str
    states: list[str]
    local_fallback: bool
    delivery_target: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "states": self.states,
            "local_fallback": self.local_fallback,
            "delivery_target": self.delivery_target,
        }


class IdempotencyStore:
    """Persist consumed cron nonces."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "cron_nonces.json"
        self._lock = FileLock(str(self.path) + ".lock")
        self._thread_lock = threading.Lock()

    def seen(self, nonce: str) -> bool:
        return nonce in self._load()

    def remember(self, nonce: str) -> None:
        # Lock the whole read-modify-write so concurrent fires never lose a
        # nonce, then commit atomically via os.replace (finding 2.2). The
        # thread lock serializes in-process threads (the FileLock is reentrant
        # per instance); the FileLock serializes across processes.
        with self._thread_lock, self._lock:
            nonces = self._load()
            nonces.add(nonce)
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"nonces": sorted(nonces)}, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # A truncated/corrupt file (e.g. crash mid-write before this fix)
            # must not poison every future verify(); treat it as "no nonces".
            return set()
        return {str(item) for item in payload.get("nonces", [])}


class HostedCronVerifier:
    """Validate hosted cron fire payloads without external services."""

    def __init__(self, audience: str, idempotency: IdempotencyStore) -> None:
        self.audience = audience
        self.idempotency = idempotency

    def fixture_payload(
        self,
        *,
        job_id: str,
        nonce: str,
        schedule_id: str = "schedule-demo",
        expires_in_seconds: int = 300,
    ) -> dict[str, Any]:
        now = int(time.time())
        return {
            "job_id": job_id,
            "schedule_id": schedule_id,
            "nonce": nonce,
            "audience": self.audience,
            "issued_at": now,
            "expiration": now + expires_in_seconds,
            "signature": {"algorithm": "fake-hmac", "value": "fake-signature"},
        }

    def verify(self, payload: dict[str, Any]) -> CronFireResult:
        if payload.get("audience") != self.audience:
            return CronFireResult("blocked", "invalid audience", dict(payload))
        if int(payload.get("expiration", 0)) < int(time.time()):
            return CronFireResult("blocked", "cron fire expired", dict(payload))
        nonce = str(payload.get("nonce", ""))
        if not nonce:
            return CronFireResult("blocked", "nonce is required", dict(payload))
        if self.idempotency.seen(nonce):
            return CronFireResult("duplicate", "nonce has already been consumed", dict(payload))
        self.idempotency.remember(nonce)
        return CronFireResult("accepted", "cron fire accepted", dict(payload))


class ScaleToZeroPlanner:
    """Build deterministic hosted wake/run/deliver/hibernate plans."""

    def plan(self, job: CronJob) -> ScaleToZeroPlan:
        return ScaleToZeroPlan(
            job_id=job.job_id,
            states=["wake", "run", "deliver", "hibernate"],
            local_fallback=True,
            delivery_target=job.delivery_target,
        )


def _slug(value: str) -> str:
    return "-".join(value.lower().split()) or "cron-job"


__all__ = [
    "CronFireResult",
    "CronJob",
    "HostedCronVerifier",
    "IdempotencyStore",
    "ScaleToZeroPlan",
    "ScaleToZeroPlanner",
]
