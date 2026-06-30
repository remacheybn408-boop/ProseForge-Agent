"""Explicit writing rule management."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


WRITING_RULES_NAME = "writing_rules.yaml"
RULE_LEVELS = {"global", "project", "chapter"}


@dataclass(frozen=True)
class WritingRule:
    """One user-declared writing constraint."""

    id: str
    text: str
    level: str = "project"
    chapter: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WritingRule":
        return cls(
            id=str(payload.get("id") or ""),
            text=str(payload.get("text") or ""),
            level=_normalize_level(str(payload.get("level") or "project")),
            chapter=str(payload.get("chapter") or ""),
            enabled=bool(payload.get("enabled", True)),
        )


class WritingRulesStore:
    """Store explicit writing rules for draft/review/rewrite evidence."""

    def __init__(self, root: str | Path, *, slug: str | None = None) -> None:
        self.root = Path(root)
        self.slug = slug
        if slug:
            self.path = self.root / "projects" / slug / WRITING_RULES_NAME
        else:
            self.path = self.root / WRITING_RULES_NAME

    def add(self, text: str, *, level: str = "project", chapter: str = "") -> WritingRule:
        rules = self._rules()
        rule = WritingRule(
            id=f"rule_{len(rules) + 1:03d}",
            text=text,
            level=_normalize_level(level),
            chapter=chapter,
        )
        rules.append(rule)
        self._write(rules)
        return rule

    def list(self) -> list[WritingRule]:
        return [rule for rule in self._rules() if rule.enabled]

    def remove(self, rule_id: str) -> dict[str, Any]:
        rules = self._rules()
        remaining = [rule for rule in rules if rule.id != rule_id]
        removed = len(remaining) != len(rules)
        self._write(remaining)
        return {"status": "ok" if removed else "missing", "id": rule_id, "removed": removed}

    def evidence(self, *, chapter: str | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for rule in self.list():
            if rule.level == "chapter" and rule.chapter and chapter != rule.chapter:
                continue
            items.append(
                {
                    "id": rule.id,
                    "type": "writing_rule",
                    "text": rule.text,
                    "level": rule.level,
                    "chapter": rule.chapter,
                    "rule": rule.to_dict(),
                }
            )
        return items

    def _rules(self) -> list[WritingRule]:
        if not self.path.exists():
            return []
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return [WritingRule.from_dict(item) for item in payload.get("rules", [])]

    def _write(self, rules: list[WritingRule]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(
                {"rules": [rule.to_dict() for rule in rules]},
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )


def _normalize_level(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").removesuffix("-level").replace("-", "_")
    normalized = normalized.replace("_", "")
    mapping = {
        "global": "global",
        "project": "project",
        "chapter": "chapter",
        "globallevel": "global",
        "projectlevel": "project",
        "chapterlevel": "chapter",
    }
    level = mapping.get(normalized)
    if level not in RULE_LEVELS:
        raise ValueError(f"unknown writing rule level {value!r}")
    return level


__all__ = ["RULE_LEVELS", "WRITING_RULES_NAME", "WritingRule", "WritingRulesStore"]
