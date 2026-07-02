"""Trajectory dataset store and research-ready JSONL export (Task 182).

Trajectories are step-by-step records of an agent session: tool calls,
LLM responses, approval decisions, subagent runs. Export is fully local
(no network) and applies redaction by policy before leaving the workspace.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..agent.events import _redact


TRAJECTORY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TrajectoryStep:
    """One recorded step in an agent session trajectory."""

    session_id: str
    turn_id: str
    step_index: int
    kind: str
    name: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    correlation_id: str = ""
    schema_version: int = TRAJECTORY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TrajectoryStore:
    """Append-only JSONL trajectory store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, step: TrajectoryStep) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(step.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        steps: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            steps.append(json.loads(line))
        return steps


class TrajectoryDatasetExporter:
    """Deterministic redacted export of trajectory steps for research use."""

    def __init__(self, store: TrajectoryStore) -> None:
        self.store = store

    def export(
        self,
        out_path: str | Path,
        *,
        format: str = "jsonl",
        redact: bool = True,
        redact_text_fields: Iterable[str] = (),
        compact_fields: Iterable[str] = (),
        kinds: Iterable[str] | None = None,
    ) -> int:
        if format != "jsonl":
            raise ValueError(f"unsupported trajectory export format {format!r}")

        text_fields = set(redact_text_fields)
        compact = set(compact_fields)
        kind_filter = set(kinds) if kinds else None

        steps = self.store.read()
        exported: list[dict[str, Any]] = []
        for step in steps:
            if kind_filter is not None and step.get("kind") not in kind_filter:
                continue
            row = dict(step)
            row.setdefault("schema_version", TRAJECTORY_SCHEMA_VERSION)
            if redact:
                row["inputs"] = _redact_with_text(row.get("inputs", {}), text_fields)
                row["outputs"] = _redact_with_text(row.get("outputs", {}), text_fields)
            for name in compact:
                row[name] = {}
            exported.append(row)

        exported.sort(
            key=lambda item: (
                str(item.get("session_id", "")),
                str(item.get("turn_id", "")),
                int(item.get("step_index", 0)),
            )
        )

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as handle:
            for row in exported:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return len(exported)


def _redact_with_text(payload: dict[str, Any], text_fields: set[str]) -> dict[str, Any]:
    redacted = _redact(payload)
    return _mask_text_fields(redacted, text_fields)


def _mask_text_fields(value: Any, text_fields: set[str]) -> Any:
    """Replace `text_fields` matches at every depth (finding 3.2)."""
    if isinstance(value, dict):
        return {
            key: "[redacted]" if key in text_fields else _mask_text_fields(item, text_fields)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask_text_fields(item, text_fields) for item in value]
    return value


__all__ = [
    "TRAJECTORY_SCHEMA_VERSION",
    "TrajectoryDatasetExporter",
    "TrajectoryStep",
    "TrajectoryStore",
]
