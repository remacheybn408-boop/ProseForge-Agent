"""Rewrite strategy library and deterministic revision artifacts."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


REWRITE_STRATEGIES = {
    "expand": "Expand the scene with additional beats",
    "condense": "Condense the chapter while preserving core action",
    "lower_dialogue": "Reduce dialogue density and convert speech to narration",
    "enhance_description": "Add concrete sensory description",
    "increase_tension": "Sharpen suspense and scene pressure",
    "simplify_language": "Simplify ornate or difficult language",
    "yu_hua_plain_narration": "Use plain, restrained narration",
    "remove_quotes": "Remove quotation marks while preserving spoken content",
    "reduce_exposition": "Cut explanatory exposition",
}


@dataclass(frozen=True)
class RewriteStrategy:
    """One available rewrite strategy."""

    name: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RewriteResult:
    """Revision artifact created by one strategy."""

    strategy: str
    chapter: str
    path: Path
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "chapter": self.chapter,
            "path": str(self.path),
            "text": self.text,
        }


class RewriteStrategyLibrary:
    """Apply named rewrite strategies to chapter drafts."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def list_strategies(self) -> list[RewriteStrategy]:
        return [RewriteStrategy(name, REWRITE_STRATEGIES[name]) for name in sorted(REWRITE_STRATEGIES)]

    def rewrite(self, *, strategy: str, chapter: str) -> RewriteResult:
        if strategy not in REWRITE_STRATEGIES:
            raise ValueError(f"unknown rewrite strategy {strategy!r}")
        source = self.project_root / "chapters" / f"{chapter}.md"
        text = source.read_text(encoding="utf-8") if source.exists() else ""
        rewritten = _TRANSFORMS[strategy](text)
        path = self.project_root / "revisions" / chapter / f"{strategy}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rewritten, encoding="utf-8")
        return RewriteResult(strategy=strategy, chapter=chapter, path=path, text=rewritten)


def _expand(text: str) -> str:
    return text.rstrip() + "\n\nThe moment stretched into another beat of action and consequence.\n"


def _condense(text: str) -> str:
    sentences = _sentences(text)
    if not sentences:
        return text
    return sentences[0].strip() + "\n"


def _lower_dialogue(text: str) -> str:
    replaced = re.sub(r'"([^"]*)"', "A brief exchange passed between them", text)
    return re.sub(r"\s+", " ", replaced).strip() + "\n"


def _enhance_description(text: str) -> str:
    return text.rstrip() + "\n\nThe air carried dust, old rain, and the faint scrape of distant footsteps.\n"


def _increase_tension(text: str) -> str:
    return "Something in the silence tightened.\n" + text


def _simplify_language(text: str) -> str:
    replacements = {
        "corridor": "hall",
        "approximately": "about",
        "utilize": "use",
        "commenced": "began",
    }
    simplified = text
    for old, new in replacements.items():
        simplified = re.sub(old, new, simplified, flags=re.IGNORECASE)
    return simplified


def _yu_hua_plain_narration(text: str) -> str:
    plain = re.sub(r"\b(very|quiet|beautiful|ornate|soft|bright|dark)\b\s*", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", plain).strip() + "\n"


def _remove_quotes(text: str) -> str:
    return text.replace('"', "").replace("\u201c", "").replace("\u201d", "")


def _reduce_exposition(text: str) -> str:
    kept = [
        sentence
        for sentence in _sentences(text)
        if not re.search(r"\b(because|history|explained|remembered)\b", sentence, flags=re.IGNORECASE)
    ]
    return (" ".join(kept) if kept else text).strip() + "\n"


def _sentences(text: str) -> list[str]:
    return [item for item in re.split(r"(?<=[.!?\u3002\uff01\uff1f])\s+", text.strip()) if item]


_TRANSFORMS: dict[str, Callable[[str], str]] = {
    "expand": _expand,
    "condense": _condense,
    "lower_dialogue": _lower_dialogue,
    "enhance_description": _enhance_description,
    "increase_tension": _increase_tension,
    "simplify_language": _simplify_language,
    "yu_hua_plain_narration": _yu_hua_plain_narration,
    "remove_quotes": _remove_quotes,
    "reduce_exposition": _reduce_exposition,
}


__all__ = ["REWRITE_STRATEGIES", "RewriteResult", "RewriteStrategy", "RewriteStrategyLibrary"]
