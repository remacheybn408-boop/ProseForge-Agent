"""Foreshadowing records and overdue checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


FORESHADOWING_NAME = "foreshadowing.yaml"
RESOLVED_STATUSES = {"resolved", "paid_off", "dropped"}


@dataclass(frozen=True)
class ForeshadowingRecord:
    """One planted clue, setup, or promised payoff."""

    id: str
    planted_chapter: str
    expected_payoff_chapter: str = ""
    status: str = "planted"
    importance: str = "medium"
    related_characters: list[str] = field(default_factory=list)
    related_plot_thread: str = ""
    resolved_chapter: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ForeshadowingRecord":
        return cls(
            id=str(payload.get("id") or ""),
            planted_chapter=str(payload.get("planted_chapter") or ""),
            expected_payoff_chapter=str(payload.get("expected_payoff_chapter") or ""),
            status=str(payload.get("status") or "planted"),
            importance=str(payload.get("importance") or "medium"),
            related_characters=[str(item) for item in payload.get("related_characters", [])],
            related_plot_thread=str(payload.get("related_plot_thread") or ""),
            resolved_chapter=str(payload.get("resolved_chapter") or ""),
        )


class ForeshadowingTracker:
    """Manage planted foreshadowing and unresolved payoff reminders."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / FORESHADOWING_NAME

    def add(
        self,
        *,
        id: str,
        planted_chapter: str,
        expected_payoff_chapter: str = "",
        status: str = "planted",
        importance: str = "medium",
        related_characters: list[str] | None = None,
        related_plot_thread: str = "",
    ) -> ForeshadowingRecord:
        record = ForeshadowingRecord(
            id=id,
            planted_chapter=planted_chapter,
            expected_payoff_chapter=expected_payoff_chapter,
            status=status,
            importance=importance,
            related_characters=list(related_characters or []),
            related_plot_thread=related_plot_thread,
        )
        records = [item for item in self._records() if item.id != id]
        records.append(record)
        self._write(records)
        return record

    def list(self) -> list[ForeshadowingRecord]:
        return sorted(self._records(), key=lambda item: (_chapter_number(item.planted_chapter) or 999999, item.id))

    def overdue(self, *, current_chapter: int, max_gap: int) -> list[dict[str, Any]]:
        overdue: list[dict[str, Any]] = []
        for record in self.list():
            if record.status.lower() in RESOLVED_STATUSES:
                continue
            planted = _chapter_number(record.planted_chapter)
            expected = _chapter_number(record.expected_payoff_chapter)
            chapters_since_planted = None if planted is None else current_chapter - planted
            past_gap = chapters_since_planted is not None and chapters_since_planted > max_gap
            past_payoff = expected is not None and current_chapter > expected
            if past_gap or past_payoff:
                overdue.append(
                    {
                        **record.to_dict(),
                        "chapters_since_planted": chapters_since_planted,
                        "max_gap": max_gap,
                        "reason": "past_expected_payoff" if past_payoff else "past_max_gap",
                    }
                )
        return overdue

    def resolve(self, id: str, *, resolved_chapter: str = "") -> dict[str, Any]:
        records = self._records()
        updated: list[ForeshadowingRecord] = []
        result: dict[str, Any] = {"status": "missing", "id": id}
        for record in records:
            if record.id != id:
                updated.append(record)
                continue
            resolved = ForeshadowingRecord(
                id=record.id,
                planted_chapter=record.planted_chapter,
                expected_payoff_chapter=record.expected_payoff_chapter,
                status="resolved",
                importance=record.importance,
                related_characters=record.related_characters,
                related_plot_thread=record.related_plot_thread,
                resolved_chapter=resolved_chapter,
            )
            updated.append(resolved)
            result = resolved.to_dict()
        self._write(updated)
        return result

    def _records(self) -> list[ForeshadowingRecord]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [ForeshadowingRecord.from_dict(item) for item in payload.get("foreshadowing", [])]

    def _write(self, records: list[ForeshadowingRecord]) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"foreshadowing": [record.to_dict() for record in records]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )


def _chapter_number(value: str) -> int | None:
    match = re.search(r"(\d+)", value or "")
    if not match:
        return None
    return int(match.group(1))


__all__ = ["FORESHADOWING_NAME", "ForeshadowingRecord", "ForeshadowingTracker"]
