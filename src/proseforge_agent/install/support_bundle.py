"""Operator support bundle assembly with redaction."""

from __future__ import annotations

import json
import os
import platform
import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .doctor import InstallationDoctor


_SENSITIVE_KEY_PARTS = ("api_key", "token", "secret", "password", "authorization")


@dataclass(frozen=True)
class SupportBundle:
    """Description of a written support bundle."""

    path: Path
    files: list[str]
    redacted: bool
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


class SupportBundleBuilder:
    """Collect read-only diagnostics into a redacted support bundle."""

    def __init__(
        self,
        root: Path | str,
        *,
        doctor: Any | None = None,
        event_log: Path | str | None = None,
    ) -> None:
        self.root = Path(root)
        self.doctor = doctor or InstallationDoctor()
        self.event_log = Path(event_log) if event_log is not None else self.root / "events.jsonl"

    def build(self, *, redact: bool = True, sources: dict[str, Any] | None = None) -> SupportBundle:
        """Write a support bundle and return its manifest."""
        bundle_dir = self.root / "support-bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        doctor_report = self.doctor.run()
        doctor_payload = doctor_report.to_dict()
        events = self._read_events()
        payload = {
            "summary": {
                "doctor_status": doctor_report.status,
                "event_count": len(events),
                "platform": platform.system() or "unknown",
            },
            "doctor": doctor_payload,
            "events": events,
            "provider_status": {"status": "not_checked"},
            "config_shape": {"workspace": str(self.root), "has_sources": bool(sources)},
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "python": platform.python_version(),
            },
            "sources": deepcopy(sources or {}),
        }
        if redact:
            payload = _redact(payload, roots=[self.root, Path.home()])

        files = []
        support_path = bundle_dir / "support-bundle.json"
        support_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        files.append(support_path.name)

        doctor_path = bundle_dir / "doctor.json"
        doctor_path.write_text(
            json.dumps(payload["doctor"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        files.append(doctor_path.name)

        events_path = bundle_dir / "events.jsonl"
        with events_path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in payload["events"]:
                handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        files.append(events_path.name)

        return SupportBundle(
            path=bundle_dir,
            files=files,
            redacted=redact,
            summary=payload["summary"],
        )

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.event_log.exists():
            return []
        rows = []
        for line in self.event_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"event_type": "unparseable", "raw": line})
        return rows


def _redact(value: Any, *, roots: list[Path]) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = _redact(item, roots=roots)
        return redacted
    if isinstance(value, list):
        return [_redact(item, roots=roots) for item in value]
    if isinstance(value, str):
        return _redact_text(value, roots)
    return value


def _redact_text(text: str, roots: list[Path]) -> str:
    redacted = text
    for root in roots:
        root_text = str(root)
        if root_text:
            redacted = redacted.replace(root_text, "[path]")
            redacted = redacted.replace(root_text.replace(os.sep, "/"), "[path]")
            redacted = redacted.replace(root_text.replace("/", os.sep), "[path]")
    redacted = re.sub(r"[A-Za-z]:/Users/[^/\s]+", "[user-home]", redacted)
    redacted = re.sub(r"[A-Za-z]:\\Users\\[^\\\s]+", "[user-home]", redacted)
    redacted = re.sub(r"(api_key|token|secret|password)=\S+", r"\1=[redacted]", redacted, flags=re.I)
    redacted = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", redacted)
    return redacted


__all__ = ["SupportBundle", "SupportBundleBuilder"]
