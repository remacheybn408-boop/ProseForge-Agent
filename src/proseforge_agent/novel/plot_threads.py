"""Plot thread tracking for long-form projects."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


PLOT_THREADS_NAME = "plot_threads.yaml"
STALE_EXEMPT_STATUSES = {"resolved", "closed", "paid_off", "dropped"}


@dataclass(frozen=True)
class PlotThread:
    """One narrative thread that should stay visible across chapters."""

    id: str
    type: str
    status: str
    first_appearance: str = ""
    last_touched: str = ""
    expected_payoff: str = ""
    linked_chapters: list[str] = field(default_factory=list)
    linked_characters: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PlotThread":
        return cls(
            id=str(payload.get("id") or ""),
            type=str(payload.get("type") or ""),
            status=str(payload.get("status") or "active"),
            first_appearance=str(payload.get("first_appearance") or ""),
            last_touched=str(payload.get("last_touched") or ""),
            expected_payoff=str(payload.get("expected_payoff") or ""),
            linked_chapters=[str(item) for item in payload.get("linked_chapters", [])],
            linked_characters=[str(item) for item in payload.get("linked_characters", [])],
        )


class PlotThreadManager:
    """Store, list, and detect stale plot threads."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / PLOT_THREADS_NAME

    def add_thread(
        self,
        *,
        id: str,
        type: str,
        status: str = "active",
        first_appearance: str = "",
        last_touched: str = "",
        expected_payoff: str = "",
        linked_chapters: list[str] | None = None,
        linked_characters: list[str] | None = None,
    ) -> PlotThread:
        thread = PlotThread(
            id=id,
            type=type,
            status=status,
            first_appearance=first_appearance,
            last_touched=last_touched,
            expected_payoff=expected_payoff,
            linked_chapters=list(linked_chapters or []),
            linked_characters=list(linked_characters or []),
        )
        threads = [item for item in self._threads() if item.id != id]
        threads.append(thread)
        self._write(threads)
        return thread

    def list(self) -> list[PlotThread]:
        return sorted(self._threads(), key=lambda item: (item.first_appearance, item.id))

    def stale(self, *, current_chapter: int, max_gap: int) -> list[dict[str, Any]]:
        stale_threads: list[dict[str, Any]] = []
        for thread in self.list():
            if thread.status.lower() in STALE_EXEMPT_STATUSES:
                continue
            last_touched = _chapter_number(thread.last_touched or thread.first_appearance)
            if last_touched is None:
                continue
            chapters_since_touched = current_chapter - last_touched
            if chapters_since_touched > max_gap:
                stale_threads.append(
                    {
                        **thread.to_dict(),
                        "chapters_since_touched": chapters_since_touched,
                        "max_gap": max_gap,
                    }
                )
        return stale_threads

    def _threads(self) -> list[PlotThread]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [PlotThread.from_dict(item) for item in payload.get("threads", [])]

    def _write(self, threads: list[PlotThread]) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"threads": [thread.to_dict() for thread in threads]},
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


__all__ = ["PLOT_THREADS_NAME", "PlotThread", "PlotThreadManager"]
