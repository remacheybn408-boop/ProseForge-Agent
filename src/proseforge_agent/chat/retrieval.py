"""Chat retrieval answers with explicit citations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ChatEvidence:
    """One retrieved evidence record available to a chat answer."""

    id: str
    source: str
    text: str
    kind: str = "context"
    score: float = 0.0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChatEvidence":
        return cls(
            id=str(payload.get("id", "")),
            source=str(payload.get("source", "")),
            text=str(payload.get("text", "")),
            kind=str(payload.get("kind", "context")),
            score=float(payload.get("score", 0.0)),
        )


@dataclass(frozen=True)
class ChatCitation:
    """A source reference attached to a generated chat answer."""

    evidence_id: str
    source: str
    quote: str


@dataclass(frozen=True)
class ChatAnswer:
    """Answer text plus machine-readable citation metadata."""

    text: str
    citations: list[ChatCitation]
    used_evidence_ids: list[str]
    degraded: bool = False
    degraded_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "citations": [asdict(citation) for citation in self.citations],
            "used_evidence_ids": list(self.used_evidence_ids),
            "degraded": self.degraded,
            "degraded_reason": self.degraded_reason,
        }


class ChatRetrievalResponder:
    """Compose a conservative answer from retrieved evidence."""

    def __init__(self, *, evidence: list[ChatEvidence] | None = None, evidence_provider=None) -> None:
        self._evidence = evidence
        self._evidence_provider = evidence_provider

    def answer(self, text: str, *, project_slug: str | None = None) -> ChatAnswer:
        evidence = self._resolve_evidence(text, project_slug)
        if not evidence:
            return ChatAnswer(
                text="No project evidence was found; this answer is degraded and needs retrieved context.",
                citations=[],
                used_evidence_ids=[],
                degraded=True,
                degraded_reason="no evidence available",
            )

        citations = [
            ChatCitation(
                evidence_id=item.id,
                source=item.source,
                quote=item.text,
            )
            for item in evidence
        ]
        cited_text = " ".join(f"{item.text} [{item.id}]" for item in evidence)
        return ChatAnswer(
            text=cited_text,
            citations=citations,
            used_evidence_ids=[item.id for item in evidence],
        )

    def _resolve_evidence(self, text: str, project_slug: str | None) -> list[ChatEvidence]:
        if self._evidence is not None:
            return list(self._evidence)
        if self._evidence_provider is None:
            return []
        raw_items = self._evidence_provider.retrieve(project_slug, text)
        evidence = []
        for item in raw_items:
            if isinstance(item, ChatEvidence):
                evidence.append(item)
            elif isinstance(item, dict):
                evidence.append(ChatEvidence.from_dict(item))
        return evidence


def render_citations(answer: ChatAnswer) -> str:
    """Render citations as parseable line-oriented source references."""
    lines = [
        f"degraded={str(answer.degraded).lower()}",
        f"used_evidence_ids={','.join(answer.used_evidence_ids)}",
    ]
    if answer.degraded_reason:
        lines.append(f"degraded_reason={answer.degraded_reason}")
    for citation in answer.citations:
        quote = citation.quote.replace("\n", " ")
        lines.append(f"{citation.evidence_id}|{citation.source}|{quote}")
    return "\n".join(lines)


__all__ = [
    "ChatAnswer",
    "ChatCitation",
    "ChatEvidence",
    "ChatRetrievalResponder",
    "render_citations",
]
