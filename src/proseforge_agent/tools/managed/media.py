"""Managed media generation and transcription tools."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Any


@dataclass(frozen=True)
class MediaArtifactRef:
    """Bounded media artifact reference."""

    id: str
    kind: str
    content_type: str
    size_bytes: int
    cost_hint: str = "fake:0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "cost_hint": self.cost_hint,
        }


@dataclass(frozen=True)
class MediaRequest:
    """Input request for fake media tools."""

    fixture: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MediaToolResult:
    """Result from a media tool call."""

    status: str
    artifact_ref: MediaArtifactRef
    reason: str = ""
    text_candidate: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    redaction_applied: bool = False
    accepted_to_canon: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "artifact_ref": self.artifact_ref.to_dict(),
            "reason": self.reason,
            "text_candidate": self.text_candidate,
            "metadata": self.metadata,
            "redaction_applied": self.redaction_applied,
            "accepted_to_canon": self.accepted_to_canon,
        }


class FakeMediaGateway:
    """Deterministic media gateway with optional degraded provider status."""

    def __init__(self, provider: str = "fake", max_input_bytes: int = 1_000_000) -> None:
        self.provider = provider
        self.max_input_bytes = max_input_bytes

    def transcribe(self, request: MediaRequest) -> MediaToolResult:
        artifact = _artifact("transcript", "text/plain", request.fixture)
        if self.provider != "fake":
            return MediaToolResult(
                status="degraded",
                artifact_ref=artifact,
                reason=f"provider {self.provider!r} is not configured",
                metadata={"fixture": request.fixture, "provider": self.provider},
                redaction_applied=True,
            )
        if int(request.metadata.get("size_bytes", 0) or 0) > self.max_input_bytes:
            return MediaToolResult(
                status="blocked",
                artifact_ref=artifact,
                reason="input exceeds media tool limit",
                metadata={"fixture": request.fixture, "limit": self.max_input_bytes},
                redaction_applied=True,
            )
        return MediaToolResult(
            status="ok",
            artifact_ref=artifact,
            text_candidate=f"Transcription candidate for {request.fixture}.",
            metadata={"fixture": request.fixture, "content_type": request.content_type, "provider": self.provider},
            redaction_applied=True,
        )

    def generate_image(self, prompt: str, *, dry_run: bool = True) -> MediaToolResult:
        safe_prompt, redacted = _redact(prompt)
        artifact = _artifact("image", "image/png", safe_prompt)
        return MediaToolResult(
            status="planned" if dry_run else "ok",
            artifact_ref=artifact,
            metadata={
                "prompt": safe_prompt,
                "provider": self.provider,
                "dry_run": dry_run,
                "capability": "image_generation",
                "cost_hint": artifact.cost_hint,
            },
            redaction_applied=redacted,
        )


def _artifact(kind: str, content_type: str, seed: str) -> MediaArtifactRef:
    raw = f"{kind}:{content_type}:{seed}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return MediaArtifactRef(
        id=f"media-{kind}-{digest}",
        kind=kind,
        content_type=content_type,
        size_bytes=len(raw),
    )


def _redact(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?i)(token|secret|api_key|password)=\S+")
    return pattern.sub(r"\1=[redacted]", text), bool(pattern.search(text))


__all__ = ["FakeMediaGateway", "MediaArtifactRef", "MediaRequest", "MediaToolResult"]
