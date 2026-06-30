"""Compile and export novel manuscripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .artifacts import ArtifactGraphStore, ArtifactRecord
from .manifest import MANIFEST_NAME
from .publishing import PublishingMetadataStore


SUPPORTED_EXPORT_FORMATS = {"txt", "markdown", "pdf", "epub"}


@dataclass(frozen=True)
class ExportResult:
    """Result of a book export."""

    status: str
    path: Path
    format: str
    chapters: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": str(self.path),
            "format": self.format,
            "chapters": list(self.chapters),
            "warnings": list(self.warnings),
        }


class BookExporter:
    """Compile manifest-listed chapters into a book artifact."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def export(
        self,
        *,
        format: str,
        chapter_range: tuple[str, str] | None = None,
        include_drafts: bool = True,
        front_matter: str | None = None,
        back_matter: str | None = None,
    ) -> ExportResult:
        normalized = "markdown" if format == "md" else format
        if normalized not in SUPPORTED_EXPORT_FORMATS:
            raise ValueError(f"unsupported export format {format!r}")
        warnings: list[str] = []
        if normalized in {"pdf", "epub"}:
            warnings.append(f"{normalized} export uses text-compatible placeholder output")
        chapters = self._selected_chapters(chapter_range)
        text = self._compile(chapters, front_matter=front_matter, back_matter=back_matter)
        suffix = "md" if normalized == "markdown" else normalized
        path = self.project_root / "exports" / f"{self.slug}.{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self._record_export(path, normalized, [chapter["id"] for chapter in chapters])
        return ExportResult("ok", path, normalized, [chapter["id"] for chapter in chapters], warnings)

    def _selected_chapters(self, chapter_range: tuple[str, str] | None) -> list[dict[str, Any]]:
        manifest = self._manifest()
        chapters = list(manifest.get("structure", {}).get("chapters", []))
        if not chapter_range:
            return chapters
        start, end = chapter_range
        selected: list[dict[str, Any]] = []
        active = False
        for chapter in chapters:
            if chapter.get("id") == start:
                active = True
            if active:
                selected.append(chapter)
            if chapter.get("id") == end:
                break
        return selected

    def _compile(
        self,
        chapters: list[dict[str, Any]],
        *,
        front_matter: str | None,
        back_matter: str | None,
    ) -> str:
        manifest = self._manifest()
        project = manifest.get("project", {})
        publishing = PublishingMetadataStore(self.root, slug=self.slug).load().data
        title = project.get("title") or self.slug
        title = publishing.get("title") or title
        author = publishing.get("pen_name") or publishing.get("author") or project.get("author") or ""
        copyright_text = publishing.get("copyright") or "Copyright"
        ai_usage = publishing.get("ai_usage_statement") or ""
        parts = [
            front_matter or f"# {title}\n\nby {author}".strip(),
            "",
            copyright_text,
            ai_usage,
            "",
            "Table of Contents",
            *[f"- {chapter.get('title') or chapter.get('id')}" for chapter in chapters],
            "",
        ]
        for chapter in chapters:
            chapter_path = Path(str(chapter.get("path") or ""))
            if not chapter_path.is_absolute():
                chapter_path = self.project_root / chapter_path if not chapter_path.exists() else chapter_path
            if not chapter_path.exists():
                chapter_path = self.project_root / "chapters" / f"{chapter.get('id')}.md"
            body = chapter_path.read_text(encoding="utf-8") if chapter_path.exists() else f"# {chapter.get('title')}"
            parts.append(body.strip())
            parts.append("")
        if back_matter:
            parts.append(back_matter)
        return "\n".join(parts).rstrip() + "\n"

    def _manifest(self) -> dict[str, Any]:
        path = self.project_root / MANIFEST_NAME
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _record_export(self, path: Path, format: str, chapters: list[str]) -> None:
        ArtifactGraphStore(self.root, slug=self.slug).add(
            ArtifactRecord(
                id=f"export_{self.slug}_{format}",
                type="export",
                depends_on=chapters,
                checksum="",
                provider="local",
                prompt_version="export-v1",
            )
        )


__all__ = ["BookExporter", "ExportResult", "SUPPORTED_EXPORT_FORMATS"]
