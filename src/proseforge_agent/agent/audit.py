"""Agent audit trail recording, export, and replay."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..chat.transcript import append_jsonl, read_jsonl
from ..errors import ConfigurationError


_SENSITIVE_KEY_EXACT = {"api_key", "apikey", "token", "secret", "password", "authorization"}
_ASSIGNMENT_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)=\S+")
_SECRET_TOKEN_RE = re.compile(r"\b(?:sk|tok)-[A-Za-z0-9_-]+")


@dataclass(frozen=True)
class AuditStep:
    """One recorded agent decision step."""

    session_id: str
    step: int
    input: str = ""
    intent: dict[str, Any] = field(default_factory=dict)
    system_prompt_version: str = ""
    evidence_pack: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: dict[str, Any] = field(default_factory=dict)
    provider: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    token_usage: dict[str, Any] = field(default_factory=dict)
    model_output: str = ""
    final_action: str = ""
    trace_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayResult:
    """Deterministic replay summary from an audit session."""

    session_id: str
    step_count: int
    final_output: str
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditTrailStore:
    """Append-only per-session audit log."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def record_turn(self, session_id: str, payload: dict[str, Any]) -> AuditStep:
        existing, _warnings = read_jsonl(self._path(session_id))
        sanitized = _redact(payload)
        step = AuditStep(
            session_id=session_id,
            step=len(existing) + 1,
            input=str(sanitized.get("input", "")),
            intent=dict(sanitized.get("intent") or {}),
            system_prompt_version=str(sanitized.get("system_prompt_version", "")),
            evidence_pack=list(sanitized.get("evidence_pack") or []),
            tool_choice=str(sanitized.get("tool_choice", "")),
            tool_args=dict(sanitized.get("tool_args") or {}),
            tool_result=dict(sanitized.get("tool_result") or {}),
            provider=dict(sanitized.get("provider") or {}),
            latency_ms=int(sanitized.get("latency_ms") or 0),
            token_usage=dict(sanitized.get("token_usage") or {}),
            model_output=str(sanitized.get("model_output", "")),
            final_action=str(sanitized.get("final_action", "")),
            trace_id=str(sanitized.get("trace_id", "")),
            created_at=str(sanitized.get("created_at") or datetime.now(UTC).isoformat()),
        )
        append_jsonl(self._path(session_id), step.to_dict())
        return step

    def list_session(self, session_id: str) -> list[AuditStep]:
        rows, warnings = read_jsonl(self._path(session_id))
        if warnings:
            raise ConfigurationError("; ".join(warnings))
        return [_step_from_dict(row) for row in rows]

    def get_step(self, session_id: str, step: int) -> AuditStep:
        for record in self.list_session(session_id):
            if record.step == step:
                return record
        raise ConfigurationError(f"audit step {step} not found for session {session_id!r}")

    def export_json(self, session_id: str) -> str:
        return json.dumps(
            [step.to_dict() for step in self.list_session(session_id)],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    def export_markdown(self, session_id: str) -> str:
        lines = [f"# Audit Session {session_id}", ""]
        for step in self.list_session(session_id):
            lines.extend(
                [
                    f"## Step {step.step}",
                    "",
                    f"- intent: {step.intent.get('name', '')}",
                    f"- provider: {step.provider.get('name', '')}",
                    f"- prompt: {step.system_prompt_version or '(unknown)'}",
                    f"- final_action: {step.final_action or '(unknown)'}",
                    "",
                    "### Input",
                    step.input or "(empty)",
                    "",
                    "### Output",
                    step.model_output or "(empty)",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    def replay(self, session_id: str) -> ReplayResult:
        steps = self.list_session(session_id)
        final_output = steps[-1].model_output if steps else ""
        actions = [step.final_action or step.intent.get("name", "") for step in steps]
        return ReplayResult(
            session_id=session_id,
            step_count=len(steps),
            final_output=final_output,
            actions=actions,
        )

    def _path(self, session_id: str) -> Path:
        return self.root / "audit" / f"{session_id}.jsonl"


def _step_from_dict(payload: dict[str, Any]) -> AuditStep:
    return AuditStep(
        session_id=str(payload.get("session_id", "")),
        step=int(payload.get("step") or 0),
        input=str(payload.get("input", "")),
        intent=dict(payload.get("intent") or {}),
        system_prompt_version=str(payload.get("system_prompt_version", "")),
        evidence_pack=list(payload.get("evidence_pack") or []),
        tool_choice=str(payload.get("tool_choice", "")),
        tool_args=dict(payload.get("tool_args") or {}),
        tool_result=dict(payload.get("tool_result") or {}),
        provider=dict(payload.get("provider") or {}),
        latency_ms=int(payload.get("latency_ms") or 0),
        token_usage=dict(payload.get("token_usage") or {}),
        model_output=str(payload.get("model_output", "")),
        final_action=str(payload.get("final_action", "")),
        trace_id=str(payload.get("trace_id", "")),
        created_at=str(payload.get("created_at", "")),
    )


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if _is_sensitive_key(lowered):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _SECRET_TOKEN_RE.sub("[redacted]", _ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}=[redacted]", value))
    return value


def _is_sensitive_key(key: str) -> bool:
    return (
        key in _SENSITIVE_KEY_EXACT
        or key.endswith("_token")
        or key.endswith("-token")
        or key.endswith("_secret")
        or key.endswith("-secret")
        or key.endswith("_password")
        or key.endswith("-password")
    )


__all__ = ["AuditStep", "AuditTrailStore", "ReplayResult"]
