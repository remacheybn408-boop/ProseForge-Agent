"""Chat-to-workflow handoff packages."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


_WRITE_PERMISSIONS = {"draft_write", "project_write", "engine_write", "system_write"}


@dataclass(frozen=True)
class HandoffPackage:
    """A proposed workflow invocation produced from chat."""

    id: str
    workflow_name: str
    request_text: str
    project_slug: str | None
    mode: str
    required_permission: str
    confirmation_required: bool
    confirmed: bool = False
    status: str = "proposed"
    inputs: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def is_runnable(self) -> bool:
        """Return true only when the package can be executed now."""
        return not self.confirmation_required or self.confirmed

    def with_confirmation(self, confirmed: bool) -> "HandoffPackage":
        return replace(self, confirmed=confirmed)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["runnable"] = self.is_runnable()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HandoffPackage":
        return cls(
            id=str(payload.get("id", "")),
            workflow_name=str(payload.get("workflow_name", "")),
            request_text=str(payload.get("request_text", "")),
            project_slug=payload.get("project_slug"),
            mode=str(payload.get("mode", "general_chat")),
            required_permission=str(payload.get("required_permission", "read_only")),
            confirmation_required=bool(payload.get("confirmation_required", False)),
            confirmed=bool(payload.get("confirmed", False)),
            status=str(payload.get("status", "proposed")),
            inputs=dict(payload.get("inputs") or {}),
            created_at=str(payload.get("created_at", "")),
        )


class ChatWorkflowHandoff:
    """Create proposed workflow packages from chat turns."""

    def create(
        self,
        text: str,
        *,
        project_slug: str | None = None,
        mode: str = "general_chat",
    ) -> HandoffPackage:
        workflow_name, permission, inputs = self._classify(text)
        return HandoffPackage(
            id=f"handoff_{uuid4().hex[:12]}",
            workflow_name=workflow_name,
            request_text=text,
            project_slug=project_slug,
            mode=mode,
            required_permission=permission,
            confirmation_required=permission in _WRITE_PERMISSIONS,
            inputs=inputs,
            created_at=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _classify(text: str) -> tuple[str, str, dict[str, Any]]:
        normalized = text.lower()
        inputs: dict[str, Any] = {}
        chapter_match = re.search(r"第?(\d+)\s*章", text)
        if chapter_match:
            inputs["chapter_no"] = int(chapter_match.group(1))
        if "继续" in text or "continue" in normalized or "resume" in normalized:
            return "workflow.continue", "project_write", inputs
        if "改稿" in text or "draft" in normalized or "chapter" in normalized:
            return "chapter.run", "draft_write", inputs
        return "report.render", "read_only", inputs


def render_handoff(package: HandoffPackage) -> list[str]:
    """Render compact handoff package lines for reports."""
    return [
        f"id={package.id}",
        f"workflow={package.workflow_name}",
        f"permission={package.required_permission}",
        f"confirmation_required={str(package.confirmation_required).lower()}",
        f"runnable={str(package.is_runnable()).lower()}",
        f"status={package.status}",
    ]


__all__ = ["ChatWorkflowHandoff", "HandoffPackage", "render_handoff"]
