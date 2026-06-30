"""Writing analytics: word-count trends, effort/cost stats, and completion prediction."""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ANALYTICS_DIR = "analytics"
LOG_NAME = "progress.jsonl"


@dataclass(frozen=True)
class DailyStat:
    """Aggregated writing activity for one date."""

    date: str
    words: int
    revisions: int
    cost: float
    minutes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalyticsSummary:
    """Project-wide writing analytics with a pace-based completion prediction."""

    total_words: int
    chapter_words: dict[str, int]
    total_revisions: int
    total_cost: float
    total_minutes: int
    days_recorded: int
    avg_daily_words: float
    target_words: int | None
    days_remaining: int | None
    daily: list[DailyStat] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["daily"] = [stat.to_dict() for stat in self.daily]
        return data


class WritingAnalytics:
    """Record and summarize writing progress for a novel project."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.log_path = self.project_root / ANALYTICS_DIR / LOG_NAME

    def record(
        self,
        date: str,
        *,
        chapter: str,
        words: int,
        revisions: int = 0,
        provider_cost: float = 0.0,
        minutes: int = 0,
    ) -> None:
        entry = {
            "date": date,
            "chapter": chapter,
            "words": int(words),
            "revisions": int(revisions),
            "cost": float(provider_cost),
            "minutes": int(minutes),
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _entries(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        entries = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
        return entries

    def daily(self) -> list[DailyStat]:
        buckets: dict[str, dict[str, float]] = {}
        for entry in self._entries():
            bucket = buckets.setdefault(entry["date"], {"words": 0, "revisions": 0, "cost": 0.0, "minutes": 0})
            bucket["words"] += entry["words"]
            bucket["revisions"] += entry["revisions"]
            bucket["cost"] += entry["cost"]
            bucket["minutes"] += entry["minutes"]
        return [
            DailyStat(
                date=date,
                words=int(bucket["words"]),
                revisions=int(bucket["revisions"]),
                cost=round(bucket["cost"], 4),
                minutes=int(bucket["minutes"]),
            )
            for date, bucket in sorted(buckets.items())
        ]

    def chapter_words(self) -> dict[str, int]:
        chapters_root = self.project_root / "chapters"
        words: dict[str, int] = {}
        if chapters_root.exists():
            for path in sorted(chapters_root.glob("*.md")):
                words[path.stem] = _word_count(path.read_text(encoding="utf-8"))
        return words

    def summary(self, *, target_words: int | None = None) -> AnalyticsSummary:
        daily = self.daily()
        total_words = sum(stat.words for stat in daily)
        total_revisions = sum(stat.revisions for stat in daily)
        total_cost = round(sum(stat.cost for stat in daily), 4)
        total_minutes = sum(stat.minutes for stat in daily)
        days_recorded = len(daily)
        avg_daily_words = round(total_words / days_recorded, 2) if days_recorded else 0.0
        days_remaining: int | None = None
        if target_words is not None and avg_daily_words > 0:
            remaining = max(0, target_words - total_words)
            days_remaining = math.ceil(remaining / avg_daily_words)
        return AnalyticsSummary(
            total_words=total_words,
            chapter_words=self.chapter_words(),
            total_revisions=total_revisions,
            total_cost=total_cost,
            total_minutes=total_minutes,
            days_recorded=days_recorded,
            avg_daily_words=avg_daily_words,
            target_words=target_words,
            days_remaining=days_remaining,
            daily=daily,
        )

    def export_csv(self) -> str:
        lines = ["date,words,revisions,cost,minutes"]
        for stat in self.daily():
            lines.append(f"{stat.date},{stat.words},{stat.revisions},{stat.cost},{stat.minutes}")
        return "\n".join(lines) + "\n"


def _word_count(text: str) -> int:
    return len(re.findall(r"\S", text))


__all__ = ["ANALYTICS_DIR", "AnalyticsSummary", "DailyStat", "WritingAnalytics"]
