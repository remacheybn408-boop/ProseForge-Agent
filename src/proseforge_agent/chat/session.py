"""Durable chat session store."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..agent.events import redact_sensitive
from ..concurrency import FileLock
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
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    messages_path: str = ""
    parent_session_id: str | None = None
    branch_name: str | None = None
    branched_from_step: int | None = None


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


@dataclass(frozen=True)
class ChatSearchResult:
    """One cross-session search hit."""

    session_id: str
    kind: str
    snippet: str
    project_slug: str | None = None
    role: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionMergeResult:
    """Summary of merging branch content into another session."""

    source_session_id: str
    target_session_id: str
    merged_count: int
    skipped_count: int
    merged_steps: list[int] = field(default_factory=list)
    skipped_steps: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionRewindResult:
    """Audit result for undo/retry transcript operations."""

    session_id: str
    operation: str
    soft_deleted_steps: list[int] = field(default_factory=list)
    source_step: int | None = None
    marker_step: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionCompressionResult:
    """Summary of an append-only context compression marker."""

    session_id: str
    source_steps: list[int]
    marker_step: int
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionUsageReport:
    """Read-only transcript usage summary."""

    session_id: str
    message_count: int
    word_count: int
    tool_call_count: int
    evidence_ref_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
            status="active",
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
        with self._file_lock():
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

    def list(
        self,
        *,
        project_slug: str | None = None,
        include_deleted: bool = False,
    ) -> list[ChatSession]:
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
            if not include_deleted and session.status == "deleted":
                continue
            sessions.append(session)
        return sorted(sessions, key=lambda item: (item.updated_at, item.id), reverse=True)

    def archive(self, session_id: str) -> ChatSession:
        return self._set_status(session_id, "archived")

    def restore(self, session_id: str) -> ChatSession:
        return self._set_status(session_id, "active")

    def pin(self, session_id: str) -> ChatSession:
        return self._set_status(session_id, "pinned")

    def delete(self, session_id: str) -> ChatSession:
        return self._set_status(session_id, "deleted")

    def cleanup(self, *, older_than_days: int) -> list[ChatSession]:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        cleaned: list[ChatSession] = []
        for session in self.list(include_deleted=True):
            if session.status in {"pinned", "deleted"}:
                continue
            updated = _parse_datetime(session.updated_at)
            if updated is not None and updated < cutoff:
                cleaned.append(self.delete(session.id))
        return sorted(cleaned, key=lambda item: item.id)

    def load_context(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        include_inactive: bool = False,
    ) -> ChatContext:
        """Load session metadata and transcript messages."""
        session = self._load_session(session_id)
        messages, warnings = self._load_messages(session)
        if not include_inactive:
            messages = [message for _, message in self._effective_step_messages(messages)]
        if limit is not None and limit >= 0:
            messages = messages[-limit:] if limit else []
        return ChatContext(session=session, messages=messages, warnings=warnings)

    def search(self, query: str, *, project_slug: str | None = None) -> list[ChatSearchResult]:
        """Search messages, tool calls, evidence refs, and decisions across sessions."""
        needle = query.lower()
        results: list[ChatSearchResult] = []
        for session in self.list(project_slug=project_slug, include_deleted=False):
            context = self.load_context(session.id)
            for index, message in enumerate(context.messages, start=1):
                source = f"{session.id}:{index}"
                if needle in message.content.lower():
                    results.append(
                        ChatSearchResult(
                            session_id=session.id,
                            project_slug=session.project_slug,
                            kind="message",
                            role=message.role,
                            snippet=_snippet(message.content, query),
                            source=source,
                        )
                    )
                for call in message.tool_calls:
                    rendered = json.dumps(call, ensure_ascii=False, sort_keys=True)
                    if needle in rendered.lower():
                        results.append(
                            ChatSearchResult(
                                session_id=session.id,
                                project_slug=session.project_slug,
                                kind="tool_call",
                                role=message.role,
                                snippet=_snippet(rendered, query),
                                source=source,
                            )
                        )
                rendered_evidence = " ".join(message.evidence_refs)
                if rendered_evidence and needle in rendered_evidence.lower():
                    results.append(
                        ChatSearchResult(
                            session_id=session.id,
                            project_slug=session.project_slug,
                            kind="evidence",
                            role=message.role,
                            snippet=_snippet(rendered_evidence, query),
                            source=source,
                        )
                    )
                rendered_metadata = json.dumps(message.provider_metadata, ensure_ascii=False, sort_keys=True)
                if rendered_metadata != "{}" and needle in rendered_metadata.lower():
                    results.append(
                        ChatSearchResult(
                            session_id=session.id,
                            project_slug=session.project_slug,
                            kind="decision",
                            role=message.role,
                            snippet=_snippet(rendered_metadata, query),
                            source=source,
                        )
                    )
        return results

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

    def export_bundle(
        self,
        session_id: str,
        *,
        include_tools: bool = True,
        include_evidence: bool = True,
        redact: bool = True,
    ) -> dict[str, Any]:
        """Export a portable, redacted session bundle."""
        context = self.load_context(session_id)
        messages: list[dict[str, Any]] = []
        for message in context.messages:
            payload = asdict(message)
            if not include_tools:
                payload["tool_calls"] = []
            if not include_evidence:
                payload["evidence_refs"] = []
            messages.append(payload)
        bundle: dict[str, Any] = {
            "format": "proseforge.chat.session",
            "version": 1,
            "session": asdict(context.session),
            "messages": messages,
            "warnings": list(context.warnings),
            "export_options": {
                "include_tools": include_tools,
                "include_evidence": include_evidence,
                "redacted": redact,
            },
        }
        return redact_sensitive(bundle) if redact else bundle

    def export_bundle_markdown(
        self,
        session_id: str,
        *,
        include_tools: bool = True,
        include_evidence: bool = True,
        redact: bool = True,
    ) -> str:
        """Export a portable session bundle as Markdown."""
        bundle = self.export_bundle(
            session_id,
            include_tools=include_tools,
            include_evidence=include_evidence,
            redact=redact,
        )
        session = bundle["session"]
        lines = [
            f"# Session Export {session['id']}",
            "",
            f"- mode: {session['mode']}",
            f"- project: {session.get('project_slug') or '(none)'}",
            f"- status: {session.get('status', 'active')}",
            "",
        ]
        for message in bundle["messages"]:
            lines.append(f"## {message['role']}")
            lines.append(str(message.get("content", "")))
            if include_evidence and message.get("evidence_refs"):
                lines.append(f"evidence: {', '.join(message['evidence_refs'])}")
            if include_tools and message.get("tool_calls"):
                lines.append("tool_calls:")
                for call in message["tool_calls"]:
                    lines.append(f"- {json.dumps(call, ensure_ascii=False, sort_keys=True)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def import_bundle(self, bundle: dict[str, Any], *, session_id: str | None = None) -> ChatSession:
        """Import a portable session bundle without overwriting existing sessions."""
        session_payload = dict(bundle.get("session") or {})
        requested_id = self._clean_session_id(session_id or str(session_payload.get("id", "")))
        target_id = self._available_import_id(requested_id)
        now = _now()
        created_at = str(session_payload.get("created_at") or now)
        updated_at = str(session_payload.get("updated_at") or created_at)
        status = str(session_payload.get("status", "active"))
        if status not in {"active", "archived", "pinned", "deleted", "branched"}:
            status = "active"
        imported = ChatSession(
            id=target_id,
            mode=str(session_payload.get("mode") or "general_chat"),
            project_slug=session_payload.get("project_slug"),
            workflow_run_id=session_payload.get("workflow_run_id"),
            title=session_payload.get("title"),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            messages_path=str(Path("chats") / target_id / "messages.jsonl"),
            parent_session_id=session_payload.get("parent_session_id"),
            branch_name=session_payload.get("branch_name"),
            branched_from_step=session_payload.get("branched_from_step"),
        )
        session_dir = self._session_dir(target_id)
        session_dir.mkdir(parents=True, exist_ok=False)
        self._messages_file(imported).touch()
        for row in bundle.get("messages") or []:
            message = self._message_from_dict(dict(row))
            append_jsonl(self._messages_file(imported), asdict(message))
        self._write_session(imported)
        return imported

    def branch(self, session_id: str, *, from_step: int, name: str) -> ChatSession:
        """Fork a session transcript through a 1-based message step."""
        if from_step < 0:
            raise ConfigurationError("branch step must be zero or greater")
        branch_name = _clean_branch_name(name)
        context = self.load_context(session_id)
        if from_step > len(context.messages):
            raise ConfigurationError(
                f"branch step {from_step} is beyond transcript length {len(context.messages)}"
            )
        branch_id = self._available_branch_id(f"{context.session.id}_{branch_name}")
        now = _now()
        branch = ChatSession(
            id=branch_id,
            mode=context.session.mode,
            project_slug=context.session.project_slug,
            workflow_run_id=context.session.workflow_run_id,
            title=branch_name,
            status="branched",
            created_at=now,
            updated_at=now,
            messages_path=str(Path("chats") / branch_id / "messages.jsonl"),
            parent_session_id=context.session.id,
            branch_name=branch_name,
            branched_from_step=from_step,
        )
        self._session_dir(branch_id).mkdir(parents=True, exist_ok=False)
        self._messages_file(branch).touch()
        for message in context.messages[:from_step]:
            append_jsonl(self._messages_file(branch), asdict(message))
        self._write_session(branch)
        return branch

    def branches(self, session_id: str) -> list[ChatSession]:
        """List child branches for a session."""
        session_id = self._clean_session_id(session_id)
        branches = [
            session
            for session in self.list(include_deleted=True)
            if session.parent_session_id == session_id and session.status != "deleted"
        ]
        return sorted(branches, key=lambda item: (item.created_at, item.id))

    def switch(self, session_id: str) -> ChatSession:
        """Validate and return the requested session branch target."""
        return self._load_session(session_id)

    def merge(
        self,
        branch_id: str,
        *,
        into_id: str,
        message_steps: list[int] | None = None,
        only_approved: bool = False,
    ) -> SessionMergeResult:
        """Merge selected branch messages into a target session."""
        branch_context = self.load_context(branch_id, include_inactive=True)
        target_context = self.load_context(into_id, include_inactive=True)
        selected_steps = set(message_steps or [])
        fork_step = branch_context.session.branched_from_step or 0
        already_merged = _merged_sources(target_context.messages)
        merged_steps: list[int] = []
        skipped_steps: list[int] = []
        for step, message in self._effective_step_messages(branch_context.messages):
            if selected_steps:
                if step not in selected_steps:
                    continue
            elif step <= fork_step:
                continue
            if (branch_context.session.id, step) in already_merged:
                skipped_steps.append(step)
                continue
            if only_approved and not _message_is_approved(message):
                skipped_steps.append(step)
                continue
            metadata = dict(message.provider_metadata)
            metadata["merge"] = {
                "source_session_id": branch_context.session.id,
                "source_step": step,
                "branch_name": branch_context.session.branch_name or "",
            }
            self.append_message(
                into_id,
                message.role,
                message.content,
                evidence_refs=list(message.evidence_refs),
                tool_calls=[dict(call) for call in message.tool_calls],
                provider_metadata=metadata,
            )
            merged_steps.append(step)
        return SessionMergeResult(
            source_session_id=branch_context.session.id,
            target_session_id=self._clean_session_id(into_id),
            merged_count=len(merged_steps),
            skipped_count=len(skipped_steps),
            merged_steps=merged_steps,
            skipped_steps=skipped_steps,
        )

    def rewind(self, session_id: str, *, steps: int = 1, reason: str = "undo") -> SessionRewindResult:
        """Record a reversible soft-delete marker for recent transcript turns."""
        context = self.load_context(session_id, include_inactive=True)
        effective_messages = self._effective_step_messages(context.messages)
        eligible_steps = [
            step
            for step, message in effective_messages
            if message.provider_metadata.get("operation") not in {"rewind", "retry", "compress"}
        ]
        soft_deleted_steps = eligible_steps[-max(0, steps) :] if steps else []
        marker = self.append_message(
            session_id,
            "system",
            f"Session rewind ({reason}): soft-deleted steps {', '.join(map(str, soft_deleted_steps)) or '(none)'}.",
            provider_metadata={
                "operation": "rewind",
                "reason": reason,
                "soft_deleted_steps": soft_deleted_steps,
                "reversible": True,
            },
        )
        return SessionRewindResult(
            session_id=self._clean_session_id(session_id),
            operation="rewind",
            soft_deleted_steps=soft_deleted_steps,
            marker_step=len(context.messages) + 1,
        )

    def retry(self, session_id: str) -> SessionRewindResult:
        """Record that the last assistant turn should be retried."""
        context = self.load_context(session_id, include_inactive=True)
        source_step = None
        for step, message in reversed(self._effective_step_messages(context.messages)):
            if message.role == "assistant" and message.provider_metadata.get("operation") is None:
                source_step = step
                break
        self.append_message(
            session_id,
            "system",
            f"Retry requested for assistant step {source_step or '(none)'}.",
            provider_metadata={"operation": "retry", "source_step": source_step, "reversible": True},
        )
        return SessionRewindResult(
            session_id=self._clean_session_id(session_id),
            operation="retry",
            source_step=source_step,
            marker_step=len(context.messages) + 1,
        )

    def compress(
        self,
        session_id: str,
        *,
        upto_step: int | None = None,
        summary: str | None = None,
    ) -> SessionCompressionResult:
        """Append a summary message with source-step evidence references."""
        context = self.load_context(session_id, include_inactive=True)
        effective_messages = self._effective_step_messages(context.messages)
        max_step = min(upto_step or len(effective_messages), len(effective_messages))
        source_steps = [step for step, _ in effective_messages[: max(0, max_step)]]
        rendered_summary = summary or f"Summary of transcript steps {', '.join(map(str, source_steps)) or '(none)'}."
        evidence_refs = [f"session:{context.session.id}:step:{step}" for step in source_steps]
        self.append_message(
            session_id,
            "system",
            rendered_summary,
            evidence_refs=evidence_refs,
            provider_metadata={"operation": "compress", "source_steps": source_steps},
        )
        return SessionCompressionResult(
            session_id=context.session.id,
            source_steps=source_steps,
            marker_step=len(context.messages) + 1,
            summary=rendered_summary,
        )

    def usage(self, session_id: str) -> SessionUsageReport:
        """Return transcript usage counts without provider calls."""
        context = self.load_context(session_id)
        return SessionUsageReport(
            session_id=context.session.id,
            message_count=len(context.messages),
            word_count=sum(len(message.content.split()) for message in context.messages),
            tool_call_count=sum(len(message.tool_calls) for message in context.messages),
            evidence_ref_count=sum(len(message.evidence_refs) for message in context.messages),
        )

    def resume(self, session_id: str) -> ChatSession:
        """Validate and return a session for terminal resume."""
        return self._load_session(session_id)

    def record_event(self, event: dict[str, Any]) -> None:
        """Append a best-effort kernel event record."""
        with self._file_lock():
            append_jsonl(self.root / "events.jsonl", {"created_at": _now(), **event})

    def save_memory_candidate(self, session_id: str, text: str) -> str:
        """Persist a candidate preference without accepting it as canon."""
        candidate_id = f"memcand_{uuid4().hex[:12]}"
        with self._file_lock():
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

    def _set_status(self, session_id: str, status: str) -> ChatSession:
        if status not in {"active", "archived", "pinned", "deleted", "branched"}:
            raise ConfigurationError(f"unsupported chat session status: {status}")
        with self._file_lock():
            session = self._load_session(session_id)
            updated = _replace_session(session, status=status, updated_at=_now())
            self._write_session(updated)
            return updated

    def _file_lock(self) -> FileLock:
        return FileLock(self.sessions_dir / ".sessions.lock")

    def _load_messages(self, session: ChatSession) -> tuple[list[ChatMessage], list[str]]:
        rows, warnings = read_jsonl(self._messages_file(session))
        return [self._message_from_dict(row) for row in rows], warnings

    @staticmethod
    def _effective_step_messages(messages: list[ChatMessage]) -> list[tuple[int, ChatMessage]]:
        hidden_steps: set[int] = set()
        for step, message in enumerate(messages, start=1):
            metadata = message.provider_metadata
            operation = metadata.get("operation")
            if operation == "rewind":
                hidden_steps.add(step)
                hidden_steps.update(_int_list(metadata.get("soft_deleted_steps")))
            elif operation == "retry":
                hidden_steps.add(step)
                source_step = _optional_int(metadata.get("source_step"))
                if source_step is not None:
                    hidden_steps.add(source_step)
            elif operation == "compress":
                hidden_steps.update(_int_list(metadata.get("source_steps")))

        effective: list[tuple[int, ChatMessage]] = []
        for step, message in enumerate(messages, start=1):
            operation = message.provider_metadata.get("operation")
            if step in hidden_steps or operation in {"rewind", "retry"}:
                continue
            effective.append((step, message))
        return effective

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

    def _available_import_id(self, session_id: str) -> str:
        candidate = self._clean_session_id(session_id)
        if not self._session_dir(candidate).exists():
            return candidate
        base = f"{candidate}_imported"
        candidate = base
        index = 2
        while self._session_dir(candidate).exists():
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def _available_branch_id(self, session_id: str) -> str:
        candidate = self._clean_session_id(session_id)
        if not self._session_dir(candidate).exists():
            return candidate
        base = candidate
        index = 2
        while self._session_dir(candidate).exists():
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    @staticmethod
    def _clean_session_id(session_id: str | None) -> str:
        if not session_id:
            raise ConfigurationError("chat session id is required")
        if any(part in session_id for part in ("/", "\\", "..")):
            raise ConfigurationError(f"unsafe chat session id: {session_id}")
        return session_id

    @staticmethod
    def _session_from_dict(payload: dict[str, Any]) -> ChatSession:
        step = payload.get("branched_from_step")
        return ChatSession(
            id=str(payload["id"]),
            mode=str(payload["mode"]),
            project_slug=payload.get("project_slug"),
            workflow_run_id=payload.get("workflow_run_id"),
            title=payload.get("title"),
            status=str(payload.get("status", "active")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            messages_path=str(payload["messages_path"]),
            parent_session_id=payload.get("parent_session_id"),
            branch_name=payload.get("branch_name"),
            branched_from_step=int(step) if step is not None else None,
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


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _snippet(text: str, query: str, *, radius: int = 80) -> str:
    lowered = text.lower()
    index = lowered.find(query.lower())
    if index < 0:
        return text[: radius * 2]
    start = max(0, index - radius)
    end = min(len(text), index + len(query) + radius)
    return text[start:end]


def _new_session_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"chat_{timestamp}_{uuid4().hex[:8]}"


def _clean_branch_name(name: str | None) -> str:
    if not name:
        raise ConfigurationError("branch name is required")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", name.strip()).strip("-")
    if not cleaned:
        raise ConfigurationError("branch name must contain a safe character")
    return cleaned


def _message_is_approved(message: ChatMessage) -> bool:
    metadata = message.provider_metadata
    if metadata.get("approved") is True:
        return True
    if str(metadata.get("status", "")).lower() in {"approved", "accepted"}:
        return True
    for call in message.tool_calls:
        if call.get("approved") is True:
            return True
        if str(call.get("status", "")).lower() in {"approved", "accepted"}:
            return True
    return False


def _merged_sources(messages: list[ChatMessage]) -> set[tuple[str, int]]:
    sources: set[tuple[str, int]] = set()
    for message in messages:
        merge = message.provider_metadata.get("merge")
        if not isinstance(merge, dict):
            continue
        source_session_id = str(merge.get("source_session_id") or "")
        source_step = _optional_int(merge.get("source_step"))
        if source_session_id and source_step is not None:
            sources.add((source_session_id, source_step))
    return sources


def _int_list(value: Any) -> set[int]:
    if not isinstance(value, list):
        return set()
    numbers: set[int] = set()
    for item in value:
        number = _optional_int(item)
        if number is not None:
            numbers.add(number)
    return numbers


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _replace_session(session: ChatSession, **changes: Any) -> ChatSession:
    payload = asdict(session)
    payload.update(changes)
    return ChatSession(**payload)


def _redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            redacted[str(key)] = "[REDACTED]" if _is_sensitive_key(str(key)) else _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    if isinstance(value, str):
        return _redact_secret_text(value)
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {"api_key", "apikey", "authorization", "password", "secret", "token"} or normalized.endswith(
        ("_token", "_secret", "_password")
    )


def _redact_secret_text(text: str) -> str:
    text = re.sub(
        r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*[^,\s]+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        text,
    )
    return re.sub(r"\b(?:sk|tok|key)-[A-Za-z0-9._-]+", "[REDACTED]", text)


__all__ = [
    "ChatContext",
    "ChatMessage",
    "ChatSearchResult",
    "ChatSession",
    "ChatSessionStore",
    "SessionCompressionResult",
    "SessionMergeResult",
    "SessionRewindResult",
    "SessionUsageReport",
]
