"""Prompt-ready evidence packs.

An evidence pack separates hard canon, active arcs, style rules, risk warnings,
and optional market notes, packs ranked items to fit a token budget, and
records why each item was included or excluded. It renders to cited Markdown or
JSON for prompts and reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from ..memory.store import MemoryStore
from .index import MemoryIndex
from .router import EvidenceItem, RetrievalRequest, RetrievalRouter

SECTION_KEYS: tuple[str, ...] = (
    "hard_canon",
    "active_arcs",
    "style_rules",
    "risk_warnings",
    "market_notes",
)

_TYPE_TO_SECTION = {
    "canon_fact": "hard_canon",
    "reader_promise": "active_arcs",
    "arc": "active_arcs",
    "style": "style_rules",
    "risk": "risk_warnings",
    "warning": "risk_warnings",
    "continuity_risk": "risk_warnings",
    "market": "market_notes",
}


def _section_for(item_type: str) -> str:
    return _TYPE_TO_SECTION.get(item_type, "hard_canon")


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _dedupe_by_source(items: list[EvidenceItem]) -> list[EvidenceItem]:
    seen: set[str] = set()
    deduped: list[EvidenceItem] = []
    for item in items:
        if item.source in seen:
            continue
        seen.add(item.source)
        deduped.append(item)
    return deduped


@dataclass
class EvidencePack:
    """A token-bounded, sectioned, cited bundle of retrieved context."""

    project_slug: str
    intent: str
    chapter_no: int | None = None
    token_budget: int = 1000
    used_tokens: int = 0
    sections: dict[str, list[EvidenceItem]] = field(default_factory=dict)
    items: list[EvidenceItem] = field(default_factory=list)
    excluded: list[EvidenceItem] = field(default_factory=list)
    degraded_reason: str = ""


class EvidencePackBuilder:
    """Build evidence packs from Agent memory for a given intent."""

    def __init__(self, store: MemoryStore, *, router: RetrievalRouter | None = None, rag_searcher=None) -> None:
        self._store = store
        self._router = router or RetrievalRouter(MemoryIndex(store))
        self._rag_searcher = rag_searcher

    def build(
        self,
        project_slug: str,
        intent: str,
        chapter_no: int | None = None,
        token_budget: int = 1000,
    ) -> EvidencePack:
        request = RetrievalRequest(
            project_slug=project_slug,
            intent=intent,
            chapter_no=chapter_no,
            token_budget=token_budget,
        )
        candidates = self._router.route(request)
        if self._rag_searcher is not None:
            query = self._router.query_for(request)
            for result in self._rag_searcher.search(query, project_slug=project_slug, top_k=10):
                source = result.metadata.get("source") or result.id
                candidates.append(
                    EvidenceItem(
                        text=result.text,
                        source=source,
                        type="rag_chunk",
                        score=result.score,
                        reason_included=f"matched RAG query {query!r} with score {result.score:g}",
                    )
                )
        candidates = _dedupe_by_source(candidates)
        candidates.sort(key=lambda item: (-item.score, item.source))

        sections: dict[str, list[EvidenceItem]] = {key: [] for key in SECTION_KEYS}
        included: list[EvidenceItem] = []
        excluded: list[EvidenceItem] = []
        used = 0

        for candidate in candidates:
            cost = _estimate_tokens(candidate.text)
            if used + cost <= token_budget:
                used += cost
                included.append(candidate)
                sections[_section_for(candidate.type)].append(candidate)
            else:
                excluded.append(
                    replace(
                        candidate,
                        reason_excluded="exceeded token budget",
                    )
                )

        degraded_reason = ""
        if not candidates:
            degraded_reason = "no memory available for retrieval"
        elif not included:
            degraded_reason = "no items fit the token budget"

        return EvidencePack(
            project_slug=project_slug,
            intent=intent,
            chapter_no=chapter_no,
            token_budget=token_budget,
            used_tokens=used,
            sections=sections,
            items=included,
            excluded=excluded,
            degraded_reason=degraded_reason,
        )

    # -- rendering -------------------------------------------------------

    def render_markdown(self, pack: EvidencePack) -> str:
        lines = [
            f"# Evidence Pack — {pack.project_slug} / {pack.intent}",
            f"_tokens {pack.used_tokens}/{pack.token_budget}_",
            "",
        ]
        if pack.degraded_reason:
            lines.append(f"> degraded: {pack.degraded_reason}")
            lines.append("")
        for key in SECTION_KEYS:
            lines.append(f"## {key}")
            section_items = pack.sections.get(key, [])
            if not section_items:
                lines.append("_(none)_")
            for item in section_items:
                lines.extend(_render_item_markdown(item))
            lines.append("")
        return "\n".join(lines)

    def render_json(self, pack: EvidencePack) -> dict:
        def dump(item: EvidenceItem) -> dict:
            return {
                "text": item.text,
                "source": item.source,
                "type": item.type,
                "score": item.score,
                "reason_included": item.reason_included,
                "reason_excluded": item.reason_excluded,
            }

        return {
            "project_slug": pack.project_slug,
            "intent": pack.intent,
            "chapter_no": pack.chapter_no,
            "token_budget": pack.token_budget,
            "used_tokens": pack.used_tokens,
            "degraded_reason": pack.degraded_reason,
            "sections": {
                key: [dump(i) for i in pack.sections.get(key, [])] for key in SECTION_KEYS
            },
            "items": [dump(i) for i in pack.items],
            "excluded": [dump(i) for i in pack.excluded],
        }


def _render_item_markdown(item: EvidenceItem) -> list[str]:
    if item.type != "rag_chunk":
        return [f"- {item.text} _(source: {item.source})_"]
    lines = [f"- RAG chunk _(source: {item.source})_", "  ```text"]
    safe_text = _prompt_safe_untrusted_text(item.text)
    lines.extend(f"  {line}" for line in safe_text.splitlines() or [""])
    lines.append("  ```")
    return lines


def _prompt_safe_untrusted_text(text: str) -> str:
    return text.replace("source:", "source\\:").replace("Source:", "Source\\:")


__all__ = ["SECTION_KEYS", "EvidencePack", "EvidencePackBuilder"]
