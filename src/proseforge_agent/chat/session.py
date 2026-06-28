"""Durable chat session store."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..errors import ConfigurationError
from .transcript import append_jsonl, read_jsonl


@dataclass(frozen=True)
class ChatSession:
    """Metadata for one durable chat session."""

    id: str
    mode: str
    project_slug: str | None = None
    workflow_run_id: str | None = None
    title: str | None = None
    created_at: str = ""
    updated_at: str = ""
    messages_path: str = ""


@dataclass(frozen=True)
class ChatMessage:
    """One persisted chat transcript message."""

    role: str
    content: str
    created_at: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatContext:
    """Loaded session context plus non-fatal transcript warnings."""

    session: ChatSession
    messages: list[ChatMessage]
    warnings: list[str] = field(default_factory=list)


class ChatSessionStore:
    """Filesystem-backed chat sessions rooted under an agent workspace directory."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.sessions_dir = self.root / "chats"

    def create(
        self,
        *,
        mode: str,
        project_slug: str | None = None,
        workflow_run_id: str | None = None,
        title: str | None = None,
        session_id: str | None = None,
    ) -> ChatSession:
        """Create an empty session and return its metadata."""
        now = _now()
        session_id = self._clean_session_id(session_id or _new_session_id())
        session_dir = self._session_dir(session_id)
        if session_dir.exists():
            raise ConfigurationError(f"chat session already exists: {session_id}")
        messages_path = str(Path("chats") / session_id / "messages.jsonl")
        session = ChatSession(
            id=session_id,
            mode=mode,
            project_slug=project_slug,
            workflow_run_id=workflow_run_id,
            title=title,
            created_at=now,
            updated_at=now,
            messages_path=messages_path,
        )
        session_dir.mkdir(parents=True, exist_ok=False)
        self._messages_file(session).touch()
        self._write_session(session)
        return session

    def ensure_session(
        self,
        session_id: str,
        mode: str,
        project_slug: str | None = None,
    ) -> ChatSession:
        """Load a session by id or create the requested id for kernel callers."""
        session_id = self._clean_session_id(session_id)
        try:
            return self._load_session(session_id)
        except ConfigurationError:
            return self.create(mode=mode, project_slug=project_slug, session_id=session_id)

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        evidence_refs: list[str] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        provider_metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Append a transcript message and update session metadata."""
        session = self._load_session(session_id)
        message = ChatMessage(
            role=role,
            content=content,
            created_at=_now(),
            evidence_refs=list(evidence_refs or []),
            tool_calls=list(tool_calls or []),
            provider_metadata=dict(provider_metadata or {}),
        )
        append_jsonl(self._messages_file(session), asdict(message))
        self._write_session(_replace_session(session, updated_at=message.created_at))
        return message

    def list(self, *, project_slug: str | None = None) -> list[ChatSession]:
        """List sessions, optionally filtered by project slug."""
        if not self.sessions_dir.exists():
            return []
        sessions = []
        for metadata_path in self.sessions_dir.glob("*/session.json"):
            try:
                session = self._session_from_dict(json.loads(metadata_path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                continue
            if project_slug is not None and session.project_slug != project_slug:
                continue
            sessions.append(session)
        return sorted(sessions, key=lambda item: (item.updated_at, item.id), reverse=True)

    def load_context(self, session_id: str, *, limit: int | None = None) -> ChatContext:
        """Load session metadata and transcript messages."""
        session = self._load_session(session_id)
        rows, warnings = read_jsonl(self._messages_file(session))
        messages = [self._message_from_dict(row) for row in rows]
        if limit is not None and limit >= 0:
            messages = messages[-limit:] if limit else []
        return ChatContext(session=session, messages=messages, warnings=warnings)

    def export_markdown(self, session_id: str) -> str:
        """Export a session transcript as Markdown."""
        context = self.load_context(session_id)
        lines = [
            f"# Chat Session {context.session.id}",
            "",
            f"- mode: {context.session.mode}",
            f"- project: {context.session.project_slug or '(none)'}",
            "",
        ]
        for message in context.messages:
            lines.append(f"## {message.role}")
            lines.append(message.content)
            if message.evidence_refs:
                lines.append(f"evidence: {', '.join(message.evidence_refs)}")
            if message.tool_calls:
                lines.append("tool_calls:")
                for call in message.tool_calls:
                    lines.append(f"- {json.dumps(call, ensure_ascii=False, sort_keys=True)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def export_json(self, session_id: str) -> dict[str, Any]:
        """Export a session transcript as a JSON-serializable object."""
        context = self.load_context(session_id)
        return {
            "session": asdict(context.session),
            "messages": [asdict(message) for message in context.messages],
            "warnings": list(context.warnings),
        }

    def record_event(self, event: dict[str, Any]) -> None:
        """Append a best-effort kernel event record."""
        append_jsonl(self.root / "events.jsonl", {"created_at": _now(), **event})

    def save_memory_candidate(self, session_id: str, text: str) -> str:
        """Persist a candidate preference without accepting it as canon."""
        candidate_id = f"memcand_{uuid4().hex[:12]}"
        append_jsonl(
            self.root / "memory_candidates.jsonl",
            {
                "id": candidate_id,
                "session_id": session_id,
                "text": text,
                "created_at": _now(),
                "status": "candidate",
            },
        )
        return candidate_id

    def _load_session(self, session_id: str) -> ChatSession:
        session_id = self._clean_session_id(session_id)
        path = self._metadata_file(session_id)
        if not path.exists():
            raise ConfigurationError(f"chat session not found: {session_id}")
        try:
            return self._session_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ConfigurationError(f"chat session metadata is invalid: {session_id}") from exc

    def _write_session(self, session: ChatSession) -> None:
        path = self._metadata_file(session.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(session), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _messages_file(self, session: ChatSession) -> Path:
        relative = Path(session.messages_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ConfigurationError(f"chat session has unsafe messages path: {session.id}")
        return self.root / relative

    def _metadata_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    def _session_dir(self, session_id: str) -> Path:
        return self.sessions_dir / self._clean_session_id(session_id)

    @staticmethod
    def _clean_session_id(session_id: str | None) -> str:
        if not session_id:
            raise ConfigurationError("chat session id is required")
        if any(part in session_id for part in ("/", "\\", "..")):
            raise ConfigurationError(f"unsafe chat session id: {session_id}")
        return session_id

    @staticmethod
    def _session_from_dict(payload: dict[str, Any]) -> ChatSession:
        return ChatSession(
            id=str(payload["id"]),
            mode=str(payload["mode"]),
            project_slug=payload.get("project_slug"),
            workflow_run_id=payload.get("workflow_run_id"),
            title=payload.get("title"),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            messages_path=str(payload["messages_path"]),
        )

    @staticmethod
    def _message_from_dict(payload: dict[str, Any]) -> ChatMessage:
        return ChatMessage(
            role=str(payload.get("role", "")),
            content=str(payload.get("content", "")),
            created_at=str(payload.get("created_at", "")),
            evidence_refs=list(payload.get("evidence_refs") or []),
            tool_calls=list(payload.get("tool_calls") or []),
            provider_metadata=dict(payload.get("provider_metadata") or {}),
        )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _new_session_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"chat_{timestamp}_{uuid4().hex[:8]}"


def _replace_session(session: ChatSession, **changes: Any) -> ChatSession:
    payload = asdict(session)
    payload.update(changes)
    return ChatSession(**payload)


__all__ = [
    "ChatContext",
    "ChatMessage",
    "ChatSession",
    "ChatSessionStore",
]
