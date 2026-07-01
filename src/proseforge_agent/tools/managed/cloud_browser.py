"""Headless/cloud browser managed tool adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any

from .url_safety import UrlSafetyPolicy


@dataclass(frozen=True)
class BrowserArtifactRef:
    """Bounded artifact reference produced by browser actions."""

    id: str
    kind: str
    content_type: str
    summary: str
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content_type": self.content_type,
            "summary": self.summary,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class BrowserActionResult:
    """Result from one browser action."""

    status: str
    action: str
    reason: str = ""
    summary: str = ""
    artifact_refs: list[BrowserArtifactRef] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "summary": self.summary,
            "artifact_refs": [ref.to_dict() for ref in self.artifact_refs],
            "trace": self.trace,
        }


class FakeCloudBrowserBackend:
    """Deterministic remote-browser backend used by tests and dry-run checks."""

    def __init__(self) -> None:
        self.current_url = ""
        self.closed = False

    def open(self, url: str) -> str:
        self.current_url = url
        return f"opened {url}"

    def snapshot(self) -> str:
        return f"<html><body><main>Snapshot for {self.current_url}</main></body></html>"

    def click(self, selector: str) -> str:
        return f"clicked {selector}"

    def type(self, selector: str, text: str) -> str:
        return f"typed {len(text)} chars into {selector}"

    def download(self, ref: str) -> bytes:
        return f"download:{self.current_url}:{ref}".encode("utf-8")

    def close(self) -> str:
        self.closed = True
        return "closed"


class CloudBrowser:
    """Typed cloud-browser wrapper with URL safety and bounded artifacts."""

    def __init__(
        self,
        *,
        backend: FakeCloudBrowserBackend | None = None,
        url_policy: UrlSafetyPolicy | None = None,
        artifact_prefix: str = "browser",
        dom_limit: int = 180,
    ) -> None:
        self.backend = backend or FakeCloudBrowserBackend()
        self.url_policy = url_policy or UrlSafetyPolicy()
        self.artifact_prefix = artifact_prefix
        self.dom_limit = dom_limit
        self._trace: list[dict[str, Any]] = []

    def open(self, url: str) -> BrowserActionResult:
        decision = self.url_policy.check(url)
        if decision.status != "allowed":
            event = {"action": "open", "url": url, "status": decision.status}
            self._trace.append(event)
            return BrowserActionResult(
                status=decision.status,
                action="open",
                reason=decision.reason,
                summary=decision.reason,
                trace=list(self._trace),
            )
        summary = self.backend.open(url)
        self._trace.append({"action": "open", "url": url, "status": "ok"})
        return self._ok("open", summary)

    def snapshot(self) -> BrowserActionResult:
        dom = self.backend.snapshot()
        artifact = _artifact_ref(self.artifact_prefix, "dom_snapshot", "text/html", dom)
        self._trace.append({"action": "snapshot", "artifact": artifact.id, "status": "ok"})
        return self._ok("snapshot", dom[: self.dom_limit], [artifact])

    def click(self, selector: str) -> BrowserActionResult:
        summary = self.backend.click(selector)
        self._trace.append({"action": "click", "selector": selector, "status": "ok"})
        return self._ok("click", summary)

    def type(self, selector: str, text: str) -> BrowserActionResult:
        summary = self.backend.type(selector, text)
        self._trace.append({"action": "type", "selector": selector, "status": "ok"})
        return self._ok("type", summary)

    def download(self, ref: str) -> BrowserActionResult:
        content = self.backend.download(ref)
        artifact = _artifact_ref(self.artifact_prefix, "download", "application/octet-stream", content)
        self._trace.append({"action": "download", "ref": ref, "artifact": artifact.id, "status": "ok"})
        return self._ok("download", f"download artifact {artifact.id}", [artifact])

    def close(self) -> BrowserActionResult:
        summary = self.backend.close()
        self._trace.append({"action": "close", "status": "ok"})
        return self._ok("close", summary)

    def _ok(
        self,
        action: str,
        summary: str,
        artifact_refs: list[BrowserArtifactRef] | None = None,
    ) -> BrowserActionResult:
        return BrowserActionResult(
            status="ok",
            action=action,
            summary=summary,
            artifact_refs=artifact_refs or [],
            trace=list(self._trace),
        )


def _artifact_ref(prefix: str, kind: str, content_type: str, content: str | bytes) -> BrowserArtifactRef:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return BrowserArtifactRef(
        id=f"{prefix}-{kind}-{digest}",
        kind=kind,
        content_type=content_type,
        summary=f"{kind} artifact {digest}",
        size_bytes=len(raw),
    )


__all__ = [
    "BrowserActionResult",
    "BrowserArtifactRef",
    "CloudBrowser",
    "FakeCloudBrowserBackend",
]
