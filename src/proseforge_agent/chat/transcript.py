"""JSONL transcript helpers for chat sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    """Append one UTF-8 JSON object to a transcript file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read JSONL rows, returning corrupt-line warnings instead of dropping context."""
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not path.exists():
        return rows, warnings
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"corrupt JSONL line {line_number}: {exc.msg}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            warnings.append(f"corrupt JSONL line {line_number}: expected object")
    return rows, warnings


__all__ = ["append_jsonl", "read_jsonl"]
