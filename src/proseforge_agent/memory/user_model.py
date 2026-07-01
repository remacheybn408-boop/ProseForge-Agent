"""Reviewable user model facts and memory candidates."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class UserModelFact:
    """Explicit reviewable user preference or working-style fact."""

    id: str
    text: str
    scope: str
    confidence: float
    source_refs: list[str]
    status: str
    last_confirmed_at: str = ""
    redaction_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "scope": self.scope,
            "confidence": self.confidence,
            "source_refs": self.source_refs,
            "status": self.status,
            "last_confirmed_at": self.last_confirmed_at,
            "redaction_applied": self.redaction_applied,
        }


class UserModelStore:
    """JSON-backed store for user facts and candidate preferences."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "user_model.json"

    def add_candidate(self, text: str, *, scope: str, source_refs: list[str], confidence: float = 0.6) -> UserModelFact:
        return self._add(text, scope=scope, source_refs=source_refs, confidence=confidence, status="candidate")

    def add_fact(self, text: str, *, scope: str, source_refs: list[str], confidence: float = 1.0) -> UserModelFact:
        return self._add(text, scope=scope, source_refs=source_refs, confidence=confidence, status="accepted")

    def facts(self, *, scope: str | None = None) -> list[UserModelFact]:
        records = [record for record in self.list() if record.status == "accepted"]
        if scope is None:
            return records
        return [record for record in records if record.scope == scope]

    def candidates(self) -> list[UserModelFact]:
        return [record for record in self.list() if record.status == "candidate"]

    def get_candidate(self, candidate_id: str) -> UserModelFact:
        for candidate in self.candidates():
            if candidate.id == candidate_id:
                return candidate
        raise KeyError(candidate_id)

    def list(self) -> list[UserModelFact]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [_from_dict(item) for item in payload.get("records", [])]

    def _add(
        self,
        text: str,
        *,
        scope: str,
        source_refs: list[str],
        confidence: float,
        status: str,
    ) -> UserModelFact:
        safe_text, redacted = _redact(text)
        record = UserModelFact(
            id=_fact_id(scope, safe_text, status),
            text=safe_text,
            scope=scope,
            confidence=confidence,
            source_refs=list(source_refs),
            status=status,
            redaction_applied=redacted,
        )
        records = {item.id: item for item in self.list()}
        records[record.id] = record
        self.path.write_text(
            json.dumps({"records": [item.to_dict() for item in sorted(records.values(), key=lambda value: value.id)]}, indent=2),
            encoding="utf-8",
        )
        return record


def _fact_id(scope: str, text: str, status: str) -> str:
    digest = hashlib.sha256(f"{scope}\n{text}\n{status}".encode("utf-8")).hexdigest()[:12]
    return f"userfact-{digest}"


def _redact(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?i)(token|secret|api_key|password)=\S+")
    return pattern.sub(r"\1=[redacted]", text), bool(pattern.search(text))


def _from_dict(payload: dict[str, Any]) -> UserModelFact:
    return UserModelFact(
        id=str(payload["id"]),
        text=str(payload["text"]),
        scope=str(payload["scope"]),
        confidence=float(payload.get("confidence", 1.0)),
        source_refs=[str(item) for item in payload.get("source_refs", [])],
        status=str(payload["status"]),
        last_confirmed_at=str(payload.get("last_confirmed_at", "")),
        redaction_applied=bool(payload.get("redaction_applied", False)),
    )


__all__ = ["UserModelFact", "UserModelStore"]
