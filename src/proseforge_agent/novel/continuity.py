"""Continuity conflict detection and resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


RESOLUTION_ACTIONS = {"keep_left", "keep_right", "merge", "mark_intentional", "defer"}


@dataclass(frozen=True)
class ContinuityConflict:
    """One detected continuity conflict."""

    id: str
    type: str
    subject: str
    key: str
    left: dict[str, Any]
    right: dict[str, Any]
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContinuityResolver:
    """Detect and resolve conflicting project facts."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.continuity_root = self.project_root / "continuity"
        self.facts_path = self.continuity_root / "facts.yaml"
        self.conflicts_path = self.continuity_root / "conflicts.yaml"
        self.audit_path = self.continuity_root / "audit.log"

    def check(self) -> list[ContinuityConflict]:
        facts = self._facts()
        conflicts: list[ContinuityConflict] = []
        seen: dict[tuple[str, str], dict[str, Any]] = {}
        for fact in facts:
            key = (str(fact.get("subject")), str(fact.get("key")))
            previous = seen.get(key)
            if previous and previous.get("value") != fact.get("value"):
                conflicts.append(
                    ContinuityConflict(
                        id=f"conflict_{len(conflicts) + 1:03d}",
                        type=_conflict_type(key[1]),
                        subject=key[0],
                        key=key[1],
                        left=previous,
                        right=fact,
                        actions=sorted(RESOLUTION_ACTIONS),
                    )
                )
            else:
                seen[key] = fact
        self._write_conflicts(conflicts)
        return conflicts

    def resolve(self, conflict_id: str, *, action: str) -> dict[str, Any]:
        if action not in RESOLUTION_ACTIONS:
            return {"status": "invalid_action", "conflict": conflict_id, "action": action}
        conflicts = self._conflicts()
        conflict = next((item for item in conflicts if item.id == conflict_id), None)
        if conflict is None:
            conflicts = self.check()
            conflict = next((item for item in conflicts if item.id == conflict_id), None)
        if conflict is None:
            return {"status": "missing", "conflict": conflict_id}
        facts = self._facts()
        facts = self._apply(facts, conflict, action)
        self._write_facts(facts)
        remaining = [item for item in conflicts if item.id != conflict_id]
        self._write_conflicts(remaining)
        self._audit(f"{conflict_id} {action}")
        return {"status": "ok", "conflict": conflict_id, "action": action}

    def _apply(
        self,
        facts: list[dict[str, Any]],
        conflict: ContinuityConflict,
        action: str,
    ) -> list[dict[str, Any]]:
        left_id = conflict.left.get("id")
        right_id = conflict.right.get("id")
        if action == "keep_left":
            return [fact for fact in facts if fact.get("id") != right_id]
        if action == "keep_right":
            return [
                ({**fact, "value": conflict.right.get("value"), "source": conflict.right.get("source")} if fact.get("id") == left_id else fact)
                for fact in facts
                if fact.get("id") != right_id
            ]
        if action == "merge":
            merged_value = f"{conflict.left.get('value')} / {conflict.right.get('value')}"
            return [
                ({**fact, "value": merged_value, "merged_from": [left_id, right_id]} if fact.get("id") == left_id else fact)
                for fact in facts
                if fact.get("id") != right_id
            ]
        if action == "mark_intentional":
            return [
                ({**fact, "intentional_conflict": True} if fact.get("id") in {left_id, right_id} else fact)
                for fact in facts
            ]
        return [
            ({**fact, "deferred_conflict": conflict.id} if fact.get("id") in {left_id, right_id} else fact)
            for fact in facts
        ]

    def _facts(self) -> list[dict[str, Any]]:
        if not self.facts_path.exists():
            return []
        payload = yaml.safe_load(self.facts_path.read_text(encoding="utf-8")) or {}
        return list(payload.get("facts", []))

    def _conflicts(self) -> list[ContinuityConflict]:
        if not self.conflicts_path.exists():
            return []
        payload = yaml.safe_load(self.conflicts_path.read_text(encoding="utf-8")) or {}
        return [ContinuityConflict(**item) for item in payload.get("conflicts", [])]

    def _write_facts(self, facts: list[dict[str, Any]]) -> None:
        self.continuity_root.mkdir(parents=True, exist_ok=True)
        self.facts_path.write_text(yaml.safe_dump({"facts": facts}, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _write_conflicts(self, conflicts: list[ContinuityConflict]) -> None:
        self.continuity_root.mkdir(parents=True, exist_ok=True)
        self.conflicts_path.write_text(
            yaml.safe_dump({"conflicts": [conflict.to_dict() for conflict in conflicts]}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def _audit(self, line: str) -> None:
        self.continuity_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {line}\n")


def _conflict_type(key: str) -> str:
    mapping = {
        "age": "character_age",
        "location": "location_name",
        "timeline": "timeline",
        "relationship": "relationship",
        "rule": "world_rule",
        "state": "item_state",
    }
    return mapping.get(key, "continuity")


__all__ = ["ContinuityConflict", "ContinuityResolver", "RESOLUTION_ACTIONS"]
