"""Provider certification records and release gate checks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


PASSED = "passed"
FAILED = "failed"
SKIPPED = "skipped"
UNVERIFIED = "unverified"


@dataclass(frozen=True)
class ProviderCertificationRecord:
    """Auditable provider certification status."""

    provider: str
    family: str = ""
    protocol: str = ""
    model: str = ""
    source_urls: list[str] = field(default_factory=list)
    checked_date: str = ""
    shape_status: str = UNVERIFIED
    smoke_status: str = UNVERIFIED
    workflow_status: str = UNVERIFIED
    capability_status: dict[str, str] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    next_refresh_due: str = ""


@dataclass(frozen=True)
class ProviderReleaseCheckResult:
    """Release gate result for required provider certifications."""

    status: str
    required: list[str]
    missing_providers: list[str] = field(default_factory=list)
    failed_providers: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == PASSED


def _validate_source_urls(provider: str, urls: list[str]) -> None:
    if not urls:
        raise ConfigurationError(f"provider {provider!r} requires at least one source URL")
    bad = [url for url in urls if not (url.startswith("https://") or url.startswith("http://"))]
    if bad:
        raise ConfigurationError(
            f"provider {provider!r} has invalid source URL(s): {', '.join(bad)}"
        )


def _default_next_refresh(checked_date: str) -> str:
    try:
        checked = date.fromisoformat(checked_date)
    except ValueError as exc:
        raise ConfigurationError(f"checked_date {checked_date!r} must be ISO yyyy-mm-dd") from exc
    return (checked + timedelta(days=30)).isoformat()


class CertificationStore:
    """JSON-file store for provider certification records."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def write(
        self,
        *,
        provider: str,
        source_urls: list[str],
        checked_date: str,
        shape_status: str,
        family: str = "",
        protocol: str = "",
        model: str = "",
        smoke_status: str = UNVERIFIED,
        workflow_status: str = UNVERIFIED,
        capability_status: dict[str, str] | None = None,
        limitations: list[str] | None = None,
        next_refresh_due: str | None = None,
    ) -> ProviderCertificationRecord:
        _validate_source_urls(provider, source_urls)
        record = ProviderCertificationRecord(
            provider=provider,
            family=family,
            protocol=protocol,
            model=model,
            source_urls=list(source_urls),
            checked_date=checked_date,
            shape_status=shape_status,
            smoke_status=smoke_status,
            workflow_status=workflow_status,
            capability_status=dict(capability_status or {}),
            limitations=list(limitations or []),
            next_refresh_due=next_refresh_due or _default_next_refresh(checked_date),
        )
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(provider).write_text(
            json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return record

    def load(self, provider: str) -> ProviderCertificationRecord | None:
        path = self._path(provider)
        if not path.exists():
            return None
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return ProviderCertificationRecord(**data)

    def list(self) -> list[ProviderCertificationRecord]:
        if not self._root.exists():
            return []
        return [
            ProviderCertificationRecord(**json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self._root.glob("*.json"))
        ]

    def _path(self, provider: str) -> Path:
        safe = provider.replace("/", "_").replace("\\", "_")
        return self._root / f"{safe}.json"


class ProviderReleaseCheck:
    """Require shape-passed records for all requested providers."""

    def __init__(self, records: CertificationStore) -> None:
        self._records = records

    def run(self, required: list[str]) -> ProviderReleaseCheckResult:
        missing: list[str] = []
        failed: list[str] = []
        for provider in required:
            record = self._records.load(provider)
            if record is None:
                missing.append(provider)
            elif record.shape_status != PASSED:
                failed.append(provider)
        status = PASSED if not missing and not failed else FAILED
        return ProviderReleaseCheckResult(
            status=status,
            required=list(required),
            missing_providers=missing,
            failed_providers=failed,
        )


__all__ = [
    "PASSED",
    "FAILED",
    "SKIPPED",
    "UNVERIFIED",
    "ProviderCertificationRecord",
    "ProviderReleaseCheckResult",
    "CertificationStore",
    "ProviderReleaseCheck",
]
