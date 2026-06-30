"""System prompt templates, session overrides, and composition."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True)
class SystemPromptTemplate:
    """Reusable system prompt template."""

    id: str
    version: str
    text: str
    changelog: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionPromptRecord:
    """System prompt selected or overridden for a session."""

    session_id: str
    template_id: str
    version: str
    text: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComposedSystemPrompt:
    """Final system prompt plus section order and version label."""

    text: str
    version: str
    sections: list[str]


class SystemPromptRegistry:
    """In-memory registry for built-in system prompt templates."""

    def __init__(self, templates: list[SystemPromptTemplate]) -> None:
        self._templates = {template.id: template for template in templates}

    @classmethod
    def builtins(cls) -> "SystemPromptRegistry":
        return cls(
            [
                SystemPromptTemplate(
                    id="professional_novel_editor",
                    version="1",
                    text="You are a professional novel editor. Preserve canon and give precise prose guidance.",
                    changelog=["initial professional editing prompt"],
                ),
                SystemPromptTemplate(
                    id="cold_editor",
                    version="1",
                    text="You are a cold, exacting editor. Be direct, specific, and unsentimental.",
                    changelog=["initial cold editing prompt"],
                ),
                SystemPromptTemplate(
                    id="creative_partner",
                    version="1",
                    text="You are a creative writing partner. Separate playful suggestions from accepted canon.",
                    changelog=["initial creative partner prompt"],
                ),
            ]
        )

    def list(self) -> list[SystemPromptTemplate]:
        return [self._templates[key] for key in sorted(self._templates)]

    def get(self, template_id: str) -> SystemPromptTemplate:
        template = self._templates.get(template_id)
        if template is None:
            raise ConfigurationError(f"unknown system prompt template {template_id!r}")
        return template


class SystemPromptStore:
    """Persist per-session system prompt selection."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root / "system_prompts" / "session_overrides.json"

    def set_session_template(
        self,
        session_id: str,
        template_id: str,
        *,
        registry: SystemPromptRegistry,
    ) -> SessionPromptRecord:
        template = registry.get(template_id)
        record = SessionPromptRecord(
            session_id=session_id,
            template_id=template.id,
            version=template.version,
            text=template.text,
            updated_at=_now(),
        )
        self._write_record(record)
        return record

    def set_session_override(self, session_id: str, text: str) -> SessionPromptRecord:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        record = SessionPromptRecord(
            session_id=session_id,
            template_id="session_override",
            version=digest,
            text=text,
            updated_at=_now(),
        )
        self._write_record(record)
        return record

    def get_session_prompt(
        self,
        session_id: str,
        registry: SystemPromptRegistry,
        *,
        default_template: str = "professional_novel_editor",
    ) -> SessionPromptRecord:
        records = self._records()
        if session_id in records:
            return _record_from_dict(records[session_id])
        template = registry.get(default_template)
        return SessionPromptRecord(
            session_id=session_id,
            template_id=template.id,
            version=template.version,
            text=template.text,
            updated_at="",
        )

    def _write_record(self, record: SessionPromptRecord) -> None:
        records = self._records()
        records[record.session_id] = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _records(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))


class SystemPromptComposer:
    """Compose the final system prompt in the documented order."""

    def __init__(self, *, registry: SystemPromptRegistry, store: SystemPromptStore) -> None:
        self.registry = registry
        self.store = store

    def compose(
        self,
        *,
        session_id: str,
        base_template: str = "professional_novel_editor",
        agent_profile: str = "",
        project_context: str = "",
        writing_rules: list[str] | None = None,
        provider_constraints: list[str] | None = None,
    ) -> ComposedSystemPrompt:
        base = self.registry.get(base_template)
        session = self.store.get_session_prompt(session_id, self.registry, default_template=base_template)
        sections: list[tuple[str, str]] = [
            ("base system prompt", base.text),
            ("agent profile", agent_profile),
            ("project context", project_context),
            ("writing rules", "\n".join(writing_rules or [])),
            ("provider constraints", "\n".join(provider_constraints or [])),
            ("session override", session.text if session.template_id != base.id else ""),
        ]
        rendered = [f"## {name}\n{text}" for name, text in sections if text]
        version = f"{base.id}@{base.version}"
        if session.template_id != base.id:
            version += f"+{session.template_id}@{session.version}"
        return ComposedSystemPrompt(
            text="\n\n".join(rendered),
            version=version,
            sections=[name for name, _text in sections],
        )


def _record_from_dict(payload: dict[str, Any]) -> SessionPromptRecord:
    return SessionPromptRecord(
        session_id=str(payload["session_id"]),
        template_id=str(payload["template_id"]),
        version=str(payload["version"]),
        text=str(payload["text"]),
        updated_at=str(payload.get("updated_at", "")),
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "ComposedSystemPrompt",
    "SessionPromptRecord",
    "SystemPromptComposer",
    "SystemPromptRegistry",
    "SystemPromptStore",
    "SystemPromptTemplate",
]
