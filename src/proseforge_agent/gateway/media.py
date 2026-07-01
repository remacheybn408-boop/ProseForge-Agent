"""Gateway-safe media and voice ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class AttachmentRecord:
    """Bounded attachment metadata safe to persist and cite."""

    kind: str
    filename: str
    status: str
    content_hash: str = ""
    content_ref: str = ""
    byte_size: int = 0
    mime_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    transcription_candidate: str = ""
    reason: str = ""
    raw_content: bytes | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["raw_content"] = None
        return payload


class MediaIngestion:
    """Create bounded records for gateway attachments."""

    def __init__(self, *, provider: str = "fake", max_bytes: int = 5_000_000) -> None:
        self.provider = provider
        self.max_bytes = max(0, max_bytes)

    def ingest(self, event_attachment: dict[str, Any]) -> AttachmentRecord:
        content = event_attachment.get("content") or b""
        if isinstance(content, str):
            content = content.encode("utf-8")
        filename = str(event_attachment.get("filename") or "attachment.bin")
        kind = str(event_attachment.get("type") or event_attachment.get("kind") or "unknown")
        mime_type = str(event_attachment.get("mime_type") or _mime_for(kind))
        byte_size = len(content)
        digest = sha256(content).hexdigest()
        metadata = {
            key: value
            for key, value in event_attachment.items()
            if key not in {"content", "type", "kind", "filename"} and not _is_sensitive_key(key)
        }
        metadata["mime_type"] = mime_type
        if byte_size > self.max_bytes:
            return AttachmentRecord(
                kind=kind,
                filename=filename,
                status="degraded",
                content_hash=digest,
                content_ref=f"sha256:{digest}",
                byte_size=byte_size,
                mime_type=mime_type,
                metadata=metadata,
                reason=f"attachment exceeds max size {self.max_bytes}",
            )
        transcription = ""
        if kind == "voice":
            transcription = self._transcribe(filename) if self.provider == "fake" else ""
        return AttachmentRecord(
            kind=kind,
            filename=filename,
            status="ok",
            content_hash=digest,
            content_ref=f"sha256:{digest}",
            byte_size=byte_size,
            mime_type=mime_type,
            metadata=metadata,
            transcription_candidate=transcription,
        )

    @staticmethod
    def _transcribe(filename: str) -> str:
        return f"fake transcription for {filename}"


def _mime_for(kind: str) -> str:
    return {
        "voice": "audio/ogg",
        "image": "image/png",
        "document": "application/octet-stream",
    }.get(kind, "application/octet-stream")


def _is_sensitive_key(key: str) -> bool:
    lowered = str(key).lower()
    return any(part in lowered for part in ("token", "secret", "password", "authorization", "api_key"))


__all__ = ["AttachmentRecord", "MediaIngestion"]
