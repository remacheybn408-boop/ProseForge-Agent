"""Bulk manuscript import for existing drafts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .artifacts import ArtifactGraphStore, ArtifactRecord
from .manifest import MANIFEST_NAME


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".docx"}
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")


@dataclass(frozen=True)
class ImportedChapter:
    """One parsed chapter."""

    id: str
    title: str
    path: Path | None = None
    source_path: Path | None = None
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path) if self.path else None
        payload["source_path"] = str(self.source_path) if self.source_path else None
        return payload


@dataclass(frozen=True)
class ImportResult:
    """Bulk import or preview result."""

    status: str
    chapters: list[ImportedChapter] = field(default_factory=list)
    raw_artifact_id: str = ""
    raw_artifact_path: Path | None = None
    warnings: list[str] = field(default_factory=list)
    preview: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "raw_artifact_id": self.raw_artifact_id,
            "raw_artifact_path": str(self.raw_artifact_path) if self.raw_artifact_path else None,
            "warnings": list(self.warnings),
            "preview": self.preview,
        }


class BulkImporter:
    """Import txt/markdown/folder manuscripts into a novel project."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def preview(self, source: str | Path) -> ImportResult:
        chapters, warnings = self._parse(source)
        return ImportResult(status="ok", chapters=chapters, warnings=warnings, preview=True)

    def import_manuscript(self, source: str | Path) -> ImportResult:
        chapters, warnings = self._parse(source)
        self.project_root.mkdir(parents=True, exist_ok=True)
        raw_artifact_id, raw_artifact_path = self._archive_raw(source)
        written = self._write_chapters(chapters)
        self._update_manifest(written)
        self._record_artifacts(raw_artifact_id, raw_artifact_path, written)
        return ImportResult(
            status="ok",
            chapters=written,
            raw_artifact_id=raw_artifact_id,
            raw_artifact_path=raw_artifact_path,
            warnings=warnings,
            preview=False,
        )

    def _parse(self, source: str | Path) -> tuple[list[ImportedChapter], list[str]]:
        path = Path(source)
        warnings: list[str] = []
        if path.is_dir():
            chapters: list[ImportedChapter] = []
            for item in sorted(path.iterdir(), key=lambda p: p.name):
                if item.suffix.lower() not in SUPPORTED_EXTENSIONS - {".docx"}:
                    continue
                parsed, item_warnings = self._parse_text(item.read_text(encoding="utf-8"), item)
                warnings.extend(item_warnings)
                chapters.extend(parsed[:1] if parsed else [])
            return self._renumber(chapters), warnings
        if path.suffix.lower() == ".docx":
            warnings.append("docx parsing is not available in minimal import; convert to markdown or txt")
            return [], warnings
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return [], [f"unsupported import format: {path.suffix}"]
        return self._parse_text(path.read_text(encoding="utf-8"), path)

    def _parse_text(self, text: str, source_path: Path) -> tuple[list[ImportedChapter], list[str]]:
        chapters: list[ImportedChapter] = []
        current_title: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_title, current_lines
            if current_title is None and not "".join(current_lines).strip():
                return
            index = len(chapters) + 1
            title = current_title or f"Chapter {index}"
            chapters.append(
                ImportedChapter(
                    id=f"ch_{index:03d}",
                    title=title,
                    source_path=source_path,
                    content="\n".join(current_lines).strip() + "\n",
                )
            )
            current_title = None
            current_lines = []

        for line in text.splitlines():
            match = HEADING_RE.match(line)
            if match:
                flush()
                current_title = match.group(1).strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        flush()
        return chapters, []

    @staticmethod
    def _renumber(chapters: list[ImportedChapter]) -> list[ImportedChapter]:
        return [
            ImportedChapter(
                id=f"ch_{index:03d}",
                title=chapter.title,
                source_path=chapter.source_path,
                content=chapter.content,
            )
            for index, chapter in enumerate(chapters, start=1)
        ]

    def _archive_raw(self, source: str | Path) -> tuple[str, Path]:
        source_path = Path(source)
        raw_dir = self.project_root / "imports" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        digest = _checksum_source(source_path)[:12]
        artifact_id = f"raw_import_{digest}"
        if source_path.is_dir():
            raw_path = raw_dir / f"{artifact_id}.txt"
            contents = []
            for item in sorted(source_path.iterdir(), key=lambda p: p.name):
                if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS - {".docx"}:
                    contents.append(f"# {item.name}\n{item.read_text(encoding='utf-8')}")
            raw_path.write_text("\n\n".join(contents), encoding="utf-8")
        else:
            raw_path = raw_dir / f"{artifact_id}{source_path.suffix.lower() or '.txt'}"
            raw_path.write_bytes(source_path.read_bytes())
        return artifact_id, raw_path

    def _write_chapters(self, chapters: list[ImportedChapter]) -> list[ImportedChapter]:
        chapters_dir = self.project_root / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        written: list[ImportedChapter] = []
        for chapter in chapters:
            path = chapters_dir / f"{chapter.id}.md"
            path.write_text(chapter.content or chapter.title, encoding="utf-8")
            written.append(
                ImportedChapter(
                    id=chapter.id,
                    title=chapter.title,
                    path=path,
                    source_path=chapter.source_path,
                    content=chapter.content,
                )
            )
        return written

    def _update_manifest(self, chapters: list[ImportedChapter]) -> None:
        path = self.project_root / MANIFEST_NAME
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
        payload = payload or {}
        structure = dict(payload.get("structure") or {})
        structure["chapters"] = [
            {"id": chapter.id, "title": chapter.title, "path": str(chapter.path)}
            for chapter in chapters
        ]
        payload["structure"] = structure
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _record_artifacts(self, raw_id: str, raw_path: Path, chapters: list[ImportedChapter]) -> None:
        graph = ArtifactGraphStore(self.root, slug=self.slug)
        graph.add(
            ArtifactRecord(
                id=raw_id,
                type="raw_import",
                checksum=_sha256(raw_path.read_bytes()),
                provider="local",
                prompt_version="manual-import",
            )
        )
        for chapter in chapters:
            graph.add(
                ArtifactRecord(
                    id=f"imported_{chapter.id}",
                    type="chapter",
                    depends_on=[raw_id],
                    checksum=_sha256((chapter.path or raw_path).read_bytes()),
                    provider="local",
                    prompt_version="manual-import",
                )
            )


def _checksum_source(path: Path) -> str:
    if path.is_dir():
        chunks = []
        for item in sorted(path.iterdir(), key=lambda p: p.name):
            if item.is_file():
                chunks.append(item.name.encode("utf-8") + item.read_bytes())
        return _sha256(b"".join(chunks))
    return _sha256(path.read_bytes())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


__all__ = ["BulkImporter", "ImportedChapter", "ImportResult", "SUPPORTED_EXTENSIONS"]
