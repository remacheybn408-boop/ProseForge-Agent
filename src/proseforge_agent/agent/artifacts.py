"""Bounded artifact storage for large tool results."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .tools import ToolResult


@dataclass(frozen=True)
class ArtifactRef:
    """Portable reference to a stored tool artifact."""

    id: str
    kind: str
    path: str
    content_type: str
    size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)
    redaction_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "path": self.path,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
            "redaction_applied": self.redaction_applied,
        }


class ArtifactStore:
    """Path-contained local store for redacted tool artifacts."""

    def __init__(self, root: str | Path, *, output_limit: int = 4096) -> None:
        self.root = Path(root)
        self.base = self.root / "tool_artifacts"
        self.output_limit = output_limit
        self.base.mkdir(parents=True, exist_ok=True)

    def write(self, kind: str, content: str | bytes, metadata: dict[str, Any] | None = None) -> ArtifactRef:
        metadata = dict(metadata or {})
        content_type = str(
            metadata.get("content_type")
            or ("application/octet-stream" if isinstance(content, bytes) else "text/plain")
        )
        redaction_applied = False
        if isinstance(content, bytes):
            stored = content
            suffix = ".bin"
        else:
            text, redaction_applied = _redact(content)
            stored = text.encode("utf-8")
            suffix = ".txt"
        digest = hashlib.sha256(stored).hexdigest()
        artifact_id = f"artifact-{kind}-{digest[:16]}"
        artifact_path = self._contained_path(f"{artifact_id}{suffix}")
        artifact_path.write_bytes(stored)
        ref = ArtifactRef(
            id=artifact_id,
            kind=kind,
            path=str(artifact_path.relative_to(self.root)),
            content_type=content_type,
            size_bytes=len(stored),
            metadata=metadata,
            redaction_applied=redaction_applied,
        )
        self._metadata_path(artifact_id).write_text(
            json.dumps(ref.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return ref

    def read(self, artifact_id: str) -> str | bytes:
        ref = self.get(artifact_id)
        if ref is None:
            raise FileNotFoundError(artifact_id)
        path = self._contained_path(Path(ref.path).name)
        content = path.read_bytes()
        if ref.content_type.startswith("text/"):
            return content.decode("utf-8")
        return content

    def get(self, artifact_id: str) -> ArtifactRef | None:
        path = self._metadata_path(artifact_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ArtifactRef(
            id=str(payload["id"]),
            kind=str(payload["kind"]),
            path=str(payload["path"]),
            content_type=str(payload["content_type"]),
            size_bytes=int(payload["size_bytes"]),
            metadata=dict(payload.get("metadata") or {}),
            redaction_applied=bool(payload.get("redaction_applied", False)),
        )

    def list(self) -> list[ArtifactRef]:
        refs = []
        for path in sorted(self.base.glob("*.meta.json")):
            refs.append(self.get(path.name.removesuffix(".meta.json")))
        return [ref for ref in refs if ref is not None]

    def cleanup(self, *, keep_last: int = 100) -> list[str]:
        refs = self.list()
        removed: list[str] = []
        for ref in refs[:-keep_last]:
            artifact_path = self._contained_path(Path(ref.path).name)
            metadata_path = self._metadata_path(ref.id)
            if artifact_path.exists():
                artifact_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            removed.append(ref.id)
        return removed

    def _metadata_path(self, artifact_id: str) -> Path:
        return self._contained_path(f"{artifact_id}.meta.json")

    def _contained_path(self, name: str) -> Path:
        root = self.base.resolve()
        path = (self.base / name).resolve()
        if path != root and root not in path.parents:
            raise ValueError("artifact path escapes store")
        return path


def summarize_tool_output(content: str | bytes, *, store: ArtifactStore, kind: str = "tool") -> ToolResult:
    ref = store.write(kind, content, {})
    if isinstance(content, bytes):
        summary = f"{kind} binary artifact {ref.id}"
        truncated = True
    else:
        summary = _redact(content)[0][: store.output_limit]
        truncated = len(content) > store.output_limit
    return ToolResult(
        ok=True,
        output=summary,
        summary=summary,
        artifact_refs=[ref],
        truncated=truncated,
        redaction_applied=ref.redaction_applied,
        provenance="artifact_store",
    )


def _redact(text: str) -> tuple[str, bool]:
    pattern = re.compile(r"(?i)(token|secret|api_key|password)=\S+")
    return pattern.sub(r"\1=[redacted]", text), bool(pattern.search(text))


__all__ = ["ArtifactRef", "ArtifactStore", "summarize_tool_output"]
