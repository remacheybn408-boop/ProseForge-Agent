"""Ingest ProseForge artifacts into reviewable memory candidates.

Raw project material never becomes canon directly: it enters as candidates,
each carrying its source and a reason, for review before it is written to the
memory store. Scanning is pure extraction and writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_PROMISE_MARKERS = ("promise", "承诺", "vow", "swear")


@dataclass(frozen=True)
class IngestionCandidate:
    """A reviewable memory candidate extracted from a project artifact."""

    project_slug: str
    source_path: Path
    source_kind: str
    extracted_text: str
    proposed_type: str
    confidence: float
    reason: str
    status: str = "candidate"


def _infer_source_kind(path: Path) -> str:
    name = path.name.lower()
    if name.startswith("chapter"):
        return "chapter"
    if name.startswith("outline"):
        return "outline"
    return "artifact"


def _infer_proposed_type(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in _PROMISE_MARKERS):
        return "reader_promise"
    return "canon_fact"


class ArtifactIngestor:
    """Extract memory candidates from project files and directories."""

    def scan_file(self, path: Path, project_slug: str) -> list[IngestionCandidate]:
        path = Path(path)
        source_kind = _infer_source_kind(path)
        candidates: list[IngestionCandidate] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            candidates.append(
                IngestionCandidate(
                    project_slug=project_slug,
                    source_path=path,
                    source_kind=source_kind,
                    extracted_text=line,
                    proposed_type=_infer_proposed_type(line),
                    confidence=0.5,
                    reason=f"extracted from {source_kind} artifact {path.name}",
                )
            )
        return candidates

    def scan_dir(self, directory: Path, project_slug: str) -> list[IngestionCandidate]:
        directory = Path(directory)
        candidates: list[IngestionCandidate] = []
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                candidates.extend(self.scan_file(path, project_slug))
        return candidates


__all__ = ["IngestionCandidate", "ArtifactIngestor"]
